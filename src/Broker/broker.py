import logging
import sys
import time
import zmq

from binascii import hexlify
from typing import List, Dict

# local
from common import MDP
from common.utils import dump, bytes_to_command


class Service(object):
	"""a single Service"""
	name = None  					# Service name
	requests = None  				# List of client requests
	waiting: List['Worker'] = None  # List of waiting workers

	def __init__(self, name):
		self.name = name
		self.requests = []
		self.waiting = []

	def __repr__(self):
		return f'Name: {self.name}, nr of reqs: {len(self.requests)}, waiting workers: {len(self.waiting)}'


class Worker(object):
	"""a Worker, idle or active"""
	identity = None  				# hex Identity of worker
	address = None  				# Address to route to
	services: List[Service] = None  # Owning service, if known
	expiry = None  					# expires at this point, unless heartbeat

	def __init__(self, identity, address, lifetime):
		self.identity = identity
		self.address = address
		self.services = []
		self.expiry = time.time() + 1e-3 * lifetime

	def __repr__(self):
		return f'identity: {self.identity}, address: {self.address}, expiry: {self.expiry}, services: {self.services}'


class MajorDomoBroker(object):
	# We'd normally pull these from config data
	INTERNAL_SERVICE_PREFIX = b"mmi."
	HEARTBEAT_INTERVAL = 2500  			# msecs
	HEARTBEAT_LIVENESS = 3  			# 3-5 is reasonable
	HEARTBEAT_EXPIRY = HEARTBEAT_INTERVAL * HEARTBEAT_LIVENESS

	# ---------------------------------------------------------------------

	ctx = None		# Our context
	socket = None   # Socket for clients & workers
	poller = None   # our Poller

	heartbeat_at = None       				# When to send HEARTBEAT
	services: Dict[bytes, Service] = None  	# known services
	workers: Dict[bytes, Worker] = None    	# known workers

	verbose = False

	# ---------------------------------------------------------------------

	def __init__(self, verbose=False):
		"""Initialize broker state."""
		self.verbose = verbose
		self.services = {}
		self.workers = {}
		self.heartbeat_at = time.time() + 1e-3 * self.HEARTBEAT_INTERVAL
		self.ctx = zmq.Context()
		self.socket = self.ctx.socket(zmq.ROUTER)
		self.socket.linger = 0
		self.poller = zmq.Poller()
		self.poller.register(self.socket, zmq.POLLIN)
		logging.basicConfig(format="%(asctime)s %(message)s",
							datefmt="%Y-%m-%d %H:%M:%S",
							level=logging.INFO)

	# ---------------------------------------------------------------------

	def mediate(self):
		"""Main broker work happens here"""
		while True:
			try:
				items = self.poller.poll(self.HEARTBEAT_INTERVAL)
			except KeyboardInterrupt:
				break  # Interrupted

			if items:
				msg = self.socket.recv_multipart()
				# if self.verbose:
				# 	logging.info("I: received message:")
				# 	dump(msg)

				sender = msg.pop(0)  	  # Frame 0 - Client/worker peer identity added by ROUTER socket
				assert b'' == msg.pop(0)  # Frame 1 - empty frame
				header = msg.pop(0)  	  # Frame 2 - header

				if MDP.C_CLIENT == header:
					self.process_client(sender, msg)
				elif MDP.W_WORKER == header:
					self.process_worker(sender, msg)
				else:
					logging.error("E: invalid message:")
					dump(msg)

			self.purge_workers()
			self.send_heartbeats()

			# print("-------------------------------------------------")
			# for v in self.services:
			# 	print(self.services[v])  # ???
			# print("-------------------------------------------------")



	def destroy(self):
		"""Disconnect all workers, destroy context."""
		while self.workers:
			self.delete_worker(self.workers.values()[0], True)
		self.ctx.destroy(0)

	def process_client(self, sender, msg):
		"""Process a request coming from a client."""
		assert len(msg) >= 2  # Service name + body
		service = msg.pop(0)  # Frame 3 - service name

		# prefix reply with return address to client
		msg = [sender, b''] + msg
		if service.startswith(self.INTERNAL_SERVICE_PREFIX):
			self.service_internal(service, msg)
		else:
			self.dispatch(self.require_service(service), msg)

	def process_worker(self, sender, msg):
		"""Process message sent to us by a worker."""
		assert len(msg) >= 1  # At least, command

		command = msg.pop(0)  # Frame 3 - the command

		worker: Worker = self.require_worker(sender)

		if MDP.W_READY == command:
			if len(msg) >= 1:
				service = msg.pop(0)  # Frame 4 - service name

				# No Reserved service name
				if service.startswith(self.INTERNAL_SERVICE_PREFIX):
					logging.info("I: NoReserved service name")
					self.delete_worker(worker, True)
				else:
					# Register service
					if self.verbose:
						logging.info(f"I: Worker subbed to: {service}, worker: {worker}")
					worker.services.append(self.require_service(service))
					self.worker_waiting(worker)
			else:
				worker.expiry = time.time() + 1e-3 * self.HEARTBEAT_EXPIRY

		elif MDP.W_REPLY == command:
			# Remove & save client return envelope and insert the
			# protocol header and service name, then rewrap envelope.

			client = msg.pop(0) 	# Frame 4 - Client identity added by ROUTER socket
			empty = msg.pop(0)  	# Frame 5 - empty frame
			reply = msg.pop(0)  	# Frame 6 - Reply message to client
			event = msg.pop(0)  	# Frame 7 - event
			if reply != b'':
				for service in worker.services:
					if service.name == event:
						msg = [client, b'', MDP.C_CLIENT, service.name] + [reply]
						self.socket.send_multipart(msg)
			self.worker_waiting(worker)

		elif MDP.W_HEARTBEAT == command:
			if self.verbose:
				logging.info(f"I: Heartbeat for worker: {worker}")
			worker.expiry = time.time() + 1e-3 * self.HEARTBEAT_EXPIRY

		elif MDP.W_DISCONNECT == command:
			self.delete_worker(worker, False)
		else:
			logging.error("E: invalid message:")
			dump(msg)

	def require_worker(self, address):
		"""Finds the worker (creates if necessary)."""
		assert (address is not None)
		identity = hexlify(address)
		worker = self.workers.get(identity)

		if worker is None:
			worker = Worker(identity, address, self.HEARTBEAT_EXPIRY)
			self.workers[identity] = worker
			if self.verbose:
				logging.info("I: registering new worker: %s", identity)

		return worker

	def require_service(self, name):
		"""Locates the service (creates if necessary)."""
		assert (name is not None)
		service = self.services.get(name)
		if service is None:
			service = Service(name)
			self.services[name] = service

		return service

	def bind(self, endpoint):
		"""Bind broker to endpoint, can call this multiple times.
		We use a single socket for both clients and workers.
		"""
		self.socket.bind(endpoint)
		logging.info("I: MDP broker/0.1.1 is active at %s", endpoint)

	def service_internal(self, service, msg):
		"""Handle internal service according to 8/MMI specification"""
		returncode = b"501"
		if b"mmi.service" == service:
			name = msg[-1]
			returncode = b"200" if name in self.services else b"404"
		msg[-1] = returncode

		# insert the protocol header and service name after the routing envelope ([client, ''])
		msg = msg[:2] + [MDP.C_CLIENT, service] + msg[2:]
		self.socket.send_multipart(msg)

	def send_heartbeats(self):
		"""Send heartbeats to idle workers if it's time"""
		if time.time() > self.heartbeat_at:
			for worker in self.workers.values():
				self.send_to_worker(worker, MDP.W_HEARTBEAT, None, None)

			self.heartbeat_at = time.time() + 1e-3 * self.HEARTBEAT_INTERVAL

	def purge_workers(self):
		"""Look for & kill expired workers.
		Workers are oldest to most recent, so we stop at the first alive worker.
		"""
		# logging.info("I: Looking for workers to kill: ")
		to_delete = []
		for w in self.workers.values():
			if w.expiry < time.time():
				to_delete.append(w)

		for w in to_delete:
			self.delete_worker(w, True)

	def delete_worker(self, worker: Worker, disconnect):
		"""Deletes worker from all data structures, and deletes worker."""
		assert worker is not None
		if disconnect:
			self.send_to_worker(worker, MDP.W_DISCONNECT, None, None)

		if self.verbose:
			logging.info("I: deleting expired worker: %s \n"
						 "\tremoving worker from services: ", worker)
		for service in worker.services:
			service.waiting.remove(worker)
			if self.verbose:
				logging.info(f"\t{service}")
		self.workers.pop(worker.identity)

	def worker_waiting(self, worker: Worker):
		"""This worker is now waiting for work."""
		# Queue to broker and service waiting lists
		for service in worker.services:
			if worker not in service.waiting:
				service.waiting.append(worker)
			worker.expiry = time.time() + 1e-3 * self.HEARTBEAT_EXPIRY
			self.dispatch(service, None)

	def dispatch(self, service: Service, msg):
		"""Dispatch requests to waiting workers as possible"""
		assert (service is not None)
		if msg is not None:  # Queue message if any
			service.requests.append(msg)
			print(f"added request to service: {service}")
		self.purge_workers()
		while service.waiting and service.requests:
			msg = service.requests.pop(0)

			for worker in service.waiting:
				print(f"Event: {service.name}, msg: {msg}")

				self.send_to_worker(worker, MDP.W_REQUEST, service.name, msg)

	def send_to_worker(self, worker, command, option, msg=None):
		"""Send message to worker.
		If message is provided, sends that message.
		"""
		if msg is None:
			msg = []
		elif not isinstance(msg, list):
			msg = [msg]

		# Stack routing and protocol envelopes to start of message and routing envelope
		if option is not None:
			msg = option if msg is None else msg + [option]
			# msg = [option] + msg
		msg = [worker.address, b'', MDP.W_WORKER, command] + msg

		if self.verbose and command != MDP.W_HEARTBEAT:
			logging.info("I: sending %r to worker", bytes_to_command(command))
			logging.info(f"\t{dump(msg)}")

		self.socket.send_multipart(msg)


def main():
	"""create and start new broker"""
	verbose = '-v' in sys.argv
	broker = MajorDomoBroker(True)
	broker.bind("tcp://*:5555")
	broker.mediate()


if __name__ == '__main__':
	main()
