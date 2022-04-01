import logging
import sys
import time
import zmq
import random

from binascii import hexlify
from typing import List, Dict

# local
from common import MDP
from common.utils import dump, bytes_to_command


class Event(object):
	"""a single Service"""
	name = None  						   		   # Service name
	requests = None  					   		   # List of client requests
	waiting: Dict[bytes, List['Consumer']] = None  # List of waiting consumers

	def __init__(self, name):
		self.name = name
		self.requests = []
		self.waiting = {b"all": []}  # Default when no group given

	def __repr__(self):
		return f'(Name: {self.name}, nr of reqs: {len(self.requests)}, waiting groups : ' \
			   f'{[(grp, len(cons)) for (grp, cons) in self.waiting.items()]})'



class Consumer(object):
	"""a consumer, idle or active"""
	identity = None  			# hex Identity of consumer
	address = None  			# Address to route to
	group = None				# Consumer group
	events: List[Event] = None  # Events subscribed to by consumer
	expiry = None  				# expires at this point, unless heartbeat

	def __init__(self, identity, address, lifetime, group=b"all"):
		self.identity = identity
		self.address = address
		self.group = group
		self.events = []
		self.expiry = time.time() + 1e-3 * lifetime

	def __repr__(self):
		return f'(identity: {self.identity}, address: {self.address}, group: {self.group}, events: {self.events})'


class MessageBroker(object):
	# We'd normally pull these from config data
	HEARTBEAT_INTERVAL = 2500  			# msecs
	HEARTBEAT_LIVENESS = 3  			# 3-5 is reasonable
	HEARTBEAT_EXPIRY = HEARTBEAT_INTERVAL * HEARTBEAT_LIVENESS

	# ---------------------------------------------------------------------

	ctx = None		# Our context
	socket = None   # Socket for clients & consumers
	poller = None   # our Poller

	heartbeat_at = None       				 # When to send HEARTBEAT
	Events: Dict[bytes, Event] = None  		 # known Events
	Consumers: Dict[bytes, Consumer] = None  # known consumers

	verbose = False

	# ---------------------------------------------------------------------

	def __init__(self, verbose=False):
		"""Initialize broker state."""
		self.verbose = verbose
		self.Events = {}
		self.Consumers = {}
		self.heartbeat_at = time.time() + 1e-3 * self.HEARTBEAT_INTERVAL
		self.ctx = zmq.Context()
		self.socket = self.ctx.socket(zmq.ROUTER)
		self.socket.linger = 0
		self.poller = zmq.Poller()
		self.poller.register(self.socket, zmq.POLLIN)
		self.mediating = True  # To be able to stop the "event loop"
		logging.basicConfig(format="%(asctime)s %(message)s",
							datefmt="%Y-%m-%d %H:%M:%S",
							level=logging.INFO)

	# ---------------------------------------------------------------------

	def mediate(self, ):
		"""Main broker work happens here"""
		while self.mediating:
			try:
				items = self.poller.poll(self.HEARTBEAT_INTERVAL)
			except KeyboardInterrupt:
				break  # Interrupted

			if items:
				msg = self.socket.recv_multipart()
				# if self.verbose:
				# 	logging.info("I: received message:")
				# 	dump(msg)

				sender = msg.pop(0)  	  # Frame 0 - Client/consumer peer identity added by ROUTER socket
				assert b'' == msg.pop(0)  # Frame 1 - empty frame
				header = msg.pop(0)  	  # Frame 2 - header

				if MDP.P_PRODUCER == header:
					self.process_producer(sender, msg)
				elif MDP.C_CONSUMER == header:
					self.process_consumer(sender, msg)
				else:
					logging.error("E: invalid message:")
					dump(msg)

			self.purge_consumers()
			self.send_heartbeats()


	def destroy(self):
		"""Disconnect all consumers, destroy context."""
		while self.Consumers:
			values = self.Consumers.values()
			self.delete_consumer(list(values)[0], True)
		self.ctx.destroy(0)

	def process_producer(self, sender, msg):
		"""Process a request coming from a client."""
		assert len(msg) >= 2  # event name + body
		event = msg.pop(0)    # Frame 3 - event name

		# prefix reply with return address to client
		msg = [sender, b''] + msg
		self.dispatch(self.require_event(event), msg)

	def process_consumer(self, sender, msg):
		"""Process message sent to us by a consumer."""
		assert len(msg) >= 1  # At least, command

		command = msg.pop(0)  # Frame 3 - the command

		consumer: Consumer = self.require_consumer(sender)

		if MDP.W_READY == command:
			if len(msg) >= 1:
				event = msg.pop(0)  # Frame 4 - event name

				# Register event
				consumer.events.append(self.require_event(event))
				self.consumer_waiting(consumer)
			else:
				consumer.expiry = time.time() + 1e-3 * self.HEARTBEAT_EXPIRY

		elif MDP.W_GROUP == command:
			assert len(msg) >= 1
			group = msg.pop(0)
			if self.verbose:
				logging.info(f"I: consumer register to group: {group}, consumer: {consumer}")
			# Assumes consumer has no subscriptions yet
			# If it does then they need to be removed from Service first
			consumer.group = group

		elif MDP.W_REPLY == command:
			# Remove & save client return envelope and insert the
			# protocol header and event name, then rewrap envelope.
			logging.info(f"I: REPLY: {msg}")
			client = msg.pop(0) 	# Frame 4 - Producer identity added by ROUTER socket
			empty = msg.pop(0)  	# Frame 5 - empty frame
			reply = msg.pop(0)  	# Frame 6 - Reply message to producer
			event = msg.pop(0)  	# Frame 7 - event
			logging.info(f"I: consumer: {consumer}")
			if reply != b'':
				for e in consumer.events:
					if e.name == event:
						msg = [client, b'', MDP.P_PRODUCER, e.name] + [reply]
						self.socket.send_multipart(msg)

			self.consumer_waiting(consumer)

		elif MDP.W_HEARTBEAT == command:
			if self.verbose:
				logging.info(f"I: Heartbeat for consumer: {consumer}")
			consumer.expiry = time.time() + 1e-3 * self.HEARTBEAT_EXPIRY

		elif MDP.W_DISCONNECT == command:
			self.delete_consumer(consumer, False)
		else:
			logging.error("E: invalid message:")
			dump(msg)

	def require_consumer(self, address):
		"""Finds the consumer (creates if necessary)."""
		assert (address is not None)
		identity = hexlify(address)
		consumer = self.Consumers.get(identity)

		if consumer is None:
			consumer = Consumer(identity, address, self.HEARTBEAT_EXPIRY)
			self.Consumers[identity] = consumer
			if self.verbose:
				logging.info(f"I: registering new consumer: {identity}")

		return consumer

	def require_event(self, name) -> Event:
		"""Locates the event (creates if necessary)."""
		assert (name is not None)
		event = self.Events.get(name)
		if event is None:
			event = Event(name)
			self.Events[name] = event
			if self.verbose:
				logging.info(f"I: registering new event: {event}")

		return event

	def bind(self, endpoint):
		"""Bind broker to endpoint, can call this multiple times.
		We use a single socket for both clients and consumers.
		"""
		self.socket.bind(endpoint)
		logging.info("I: MDP broker/0.1.1 is active at %s", endpoint)

	def send_heartbeats(self):
		"""Send heartbeats to idle consumers if it's time"""
		if time.time() > self.heartbeat_at:
			for consumer in self.Consumers.values():
				self.send_to_consumer(consumer, MDP.W_HEARTBEAT, None, None)

			self.heartbeat_at = time.time() + 1e-3 * self.HEARTBEAT_INTERVAL

	def purge_consumers(self):
		"""Look for & kills expired consumers.
		consumers are oldest to most recent, so we stop at the first alive consumer.
		"""
		to_delete = []
		for consumer in self.Consumers.values():
			if consumer.expiry < time.time():
				to_delete.append(consumer)

		for consumer in to_delete:
			self.delete_consumer(consumer, True)

	def delete_consumer(self, consumer: Consumer, disconnect):
		"""Deletes consumer from all data structures, and deletes consumer instance."""
		assert consumer is not None
		if disconnect:
			self.send_to_consumer(consumer, MDP.W_DISCONNECT, None, None)

		if self.verbose:
			logging.info("I: deleting expired consumer: %s \n"
						 "\tremoving consumer from event: ", consumer)
		for event in consumer.events:
			try:
				event.waiting[consumer.group].remove(consumer)
			except ValueError as e:
				logging.warning(f"W: consumer not in event: {event}\n{e} ")
			if self.verbose:
				logging.info(f"\t{event}")
		self.Consumers.pop(consumer.identity)

	def consumer_waiting(self, consumer: Consumer):
		"""This consumer is now waiting for work."""
		# Queue to broker and event waiting lists
		for event in consumer.events:
			if consumer.group in event.waiting:
				if consumer not in event.waiting[consumer.group]:
					event.waiting[consumer.group].append(consumer)
					if self.verbose:
						logging.info(f"I: Register consumer to event: {event}, consumer:  {consumer}")
			else:
				event.waiting[consumer.group] = [consumer]
				if self.verbose:
					logging.info(f"I: Register consumer to event: {event}, consumer:  {consumer}")

			consumer.expiry = time.time() + 1e-3 * self.HEARTBEAT_EXPIRY
			self.dispatch(event, None)

	def dispatch(self, event: Event, msg):
		"""Dispatch requests to waiting consumers as possible"""
		assert (event is not None)

		if msg is not None:  # Adds message to queue if any
			event.requests.append(msg)
			if self.verbose:
				logging.info(f"I: added request to service: {event}")

		self.purge_consumers()
		# Looping while there are available consumers in groups and requests queued
		while range(0, len(event.requests)):
			msg = event.requests.pop(0)
			handle = []
			for grp, consumers in event.waiting.items():
				if consumers:  # Checks if there is consumers a
					if grp == "all":
						for w in consumers:
							handle.append(w)
					else:
						w = random.choice(consumers)
						handle.append(w)

			if handle:
				for w in handle:
					self.send_to_consumer(w, MDP.W_REQUEST, event.name, msg)
			else:
				event.requests.insert(0, msg)
				logging.debug("d: Breaking, no consumers")
				break  # No consumers available on service

	def send_to_consumer(self, consumer: Consumer, command, option, msg=None):
		"""Send message to consumer.
		If message is provided, sends that message.
		"""
		if msg is None:
			msg = []
		elif not isinstance(msg, list):
			msg = [msg]

		# Stack routing and protocol envelopes to start of message and routing envelope
		if option is not None:
			# msg = option if msg is None else msg + [option]
			msg = msg + [option]
		msg = [consumer.address, b'', MDP.C_CONSUMER, command] + msg

		if self.verbose and command != MDP.W_HEARTBEAT:
			logging.info("I: sending %r to consumer", bytes_to_command(command))
			logging.info(f"\t{dump(msg)}")

		self.socket.send_multipart(msg)


def main():
	"""create and start new broker"""
	verbose = '-v' in sys.argv
	broker = MessageBroker(True)
	broker.bind("tcp://*:5555")
	broker.mediate()


if __name__ == '__main__':
	main()
