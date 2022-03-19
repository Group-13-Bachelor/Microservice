import logging
import time
import zmq

# Local
from typing import Tuple, Optional

from common import MDP
from common.utils import dump, bytes_to_command


class Service(object):
    HEARTBEAT_LIVENESS = 5  # 3-5 is reasonable
    broker = None           # Broker address
    ctx = None              # ZMQ context
    handler = None          # Socket to broker
    service = []            # Name of service
    current_service = None  # Service to reply to

    heartbeat_at = 0        # When to send HEARTBEAT (relative to time.time(), so in seconds)
    liveness = 0            # How many attempts left
    heartbeat = 2500        # Heartbeat delay, msecs
    reconnect = 2500        # Reconnect delay, msecs

    # Internal state
    timeout = 1000          # poller timeout
    verbose = False         # Print activity to stdout
    reply_to = None         # Return address

    def __init__(self, broker, verbose=False):
        self.broker = broker
        self.verbose = verbose
        self.ctx = zmq.Context()
        self.poller = zmq.Poller()
        logging.basicConfig(format="%(asctime)s %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S",
                            level=logging.INFO)
        self.reconnect_to_broker()


    def reconnect_to_broker(self):
        """Connect or reconnect to broker"""
        if self.handler:
            self.poller.unregister(self.handler)
            self.handler.close()
        self.handler = self.ctx.socket(zmq.DEALER)
        self.handler.linger = 0
        self.handler.connect(self.broker)
        self.poller.register(self.handler, zmq.POLLIN)
        if self.verbose:
            logging.info(f"I: connecting to broker at {self.broker}...")

        # Register worker
        self.send_to_broker(MDP.W_READY, None, [])
        time.sleep(2)

        # Register subscriptions
        for service in self.service:
            if self.verbose:
                logging.info(f"I: Subscribing to {service}")
            self.send_to_broker(MDP.W_READY, service, [])

        # If liveness hits zero, queue is considered disconnected
        self.liveness = self.HEARTBEAT_LIVENESS
        self.heartbeat_at = time.time() + 1e-3 * self.heartbeat


    def send_to_broker(self, command, option=None, msg=None):
        """Send message to broker.
        If no msg is provided, creates one internally
        """
        if msg is None:
            msg = []
        elif not isinstance(msg, list):
            msg = [msg]

        if option:
            msg = [option] + msg

        # Adds Frames to start of message:
        # Frame 0 - Empty frame
        # Frame 1 - header; “MDPW01” (six bytes, representing MDP/Worker v0.1)
        # Frame 2 - command
        msg = [b'', MDP.W_WORKER, command] + msg
        # if self.verbose and command != MDP.W_HEARTBEAT:
        if self.verbose:
            if command != MDP.W_HEARTBEAT:
                logging.info(f"I: sending {bytes_to_command(command)} to broker\n"
                             f"\t{msg}")
            else:
                logging.info(f"I: sending {bytes_to_command(command)} to broker")
        self.handler.send_multipart(msg)

    def subscribe(self, event: bytes):
        self.service.append(event)
        self.send_to_broker(MDP.W_READY, event, [])

    def reply(self, msg: bytes):
        """Format and send reply to client"""
        assert self.reply_to is not None
        assert self.current_service is not None
        if msg is None:
            msg = []
        elif not isinstance(msg, list):
            msg = [msg]
        # Creating W_REPLY message consisting of:
        # Frame 3 - Client address (envelope stack)
        # Frame 4 - Empty frame (envelope delimiter)
        # Frame 5 - Reply body
        reply = [self.reply_to, b''] + msg + [self.current_service]
        self.send_to_broker(MDP.W_REPLY, msg=reply)
        self.current_service = None

    def recv(self) -> Optional[Tuple[bytes, bytes]]:
        """waits for next request from broker"""
        while True:
            # Poll socket for a reply, with timeout
            try:
                items = self.poller.poll(self.timeout)
            except KeyboardInterrupt:
                break  # Interrupted


            if items:
                msg = self.handler.recv_multipart()

                self.liveness = self.HEARTBEAT_LIVENESS

                assert len(msg) >= 3
                assert b'' == msg.pop(0)            # Frame 0 - empty frame
                assert MDP.W_WORKER == msg.pop(0)   # Frame 1 - header
                command = msg.pop(0)                # Frame 2 - one byte, representing type of Command
                if self.verbose:
                    logging.info("I: received %s from broker: ", bytes_to_command(command))

                if command == MDP.W_REQUEST:
                    self.reply_to = msg.pop(0)      # Frame 3 - Client address (envelope stack)
                    assert b'' == msg.pop(0)        # Frame 4 - Empty frame (envelope delimiter)
                    req = msg.pop(0)                # Frame 5 - Request body
                    event = msg.pop(0)              # Frame 6 - event name
                    self.current_service = event
                    return req, event

                elif command == MDP.W_HEARTBEAT:
                    pass  # Do nothing for heartbeats

                elif command == MDP.W_DISCONNECT:
                    self.reconnect_to_broker()

                else:
                    logging.error("E: invalid input message: ")
                    dump(msg)

            else:
                self.liveness -= 1
                if self.verbose:
                    logging.info(f"I: liveness: {self.liveness}")
                if self.liveness == 0:
                    logging.warning("W: disconnected from broker - retrying...")
                    try:
                        time.sleep(1e-3*self.reconnect)
                    except KeyboardInterrupt:
                        break
                    logging.debug("D: reconnecting to broker...")
                    self.reconnect_to_broker()

            # Send HEARTBEAT if it's time
            if time.time() > self.heartbeat_at:
                self.send_to_broker(MDP.W_HEARTBEAT)
                self.heartbeat_at = time.time() + 1e-3*self.heartbeat

        logging.warning("W: interrupt received, killing worker...")
        return (None, None)


    def destroy(self):
        # context.destroy depends on pyzmq >= 2.1.10
        self.ctx.destroy(0)
