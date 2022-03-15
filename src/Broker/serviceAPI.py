"""Majordomo Protocol Worker API, Python version
Implements the MDP/Worker spec at http:#rfc.zeromq.org/spec:7.
Author: Min RK <benjaminrk@gmail.com>
Based on Java example by Arkadiusz Orzechowski
"""

import logging
import time
import zmq

from utils import dump, bytes_to_command
import MDP


class Service(object):
    """Majordomo Protocol Worker API, Python version
    Implements the MDP/Worker spec at http:#rfc.zeromq.org/spec:7.
    """

    HEARTBEAT_LIVENESS = 3  # 3-5 is reasonable
    broker = None       # Broker address
    ctx = None          # ZMQ context
    socket = None       # Socket to broker
    service = None      # Name of service


    heartbeat_at = 0  # When to send HEARTBEAT (relative to time.time(), so in seconds)
    liveness = 0      # How many attempts left
    heartbeat = 2500  # Heartbeat delay, msecs
    reconnect = 2500  # Reconnect delay, msecs

    # Internal state
    timeout = 1000        # poller timeout
    verbose = False       # Print activity to stdout
    # expect_reply = False  # False only at start
    reply_to = None       # Return address

    def __init__(self, broker, service, verbose=False):
        self.broker = broker
        self.service = service
        self.verbose = verbose
        self.ctx = zmq.Context()
        self.poller = zmq.Poller()
        logging.basicConfig(format="%(asctime)s %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S",
                            level=logging.INFO)
        self.reconnect_to_broker()


    def reconnect_to_broker(self):
        """Connect or reconnect to broker"""
        if self.socket:
            self.poller.unregister(self.socket)
            self.socket.close()
        self.socket = self.ctx.socket(zmq.DEALER)
        self.socket.linger = 0
        self.socket.connect(self.broker)
        self.poller.register(self.socket, zmq.POLLIN)
        if self.verbose:
            logging.info("I: connecting to broker at %s...", self.broker)

        # Register service with broker
        self.send_to_broker(MDP.W_READY, self.service, [])
        time.sleep(1)

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
        # Frame 1 - “MDPW01” (six bytes, representing MDP/Worker v0.1)
        # Frame 2 - command
        msg = [b'', MDP.W_WORKER, command] + msg
        # if self.verbose and command != MDP.W_HEARTBEAT:
        if self.verbose:
            logging.info("I: sending %s to broker", bytes_to_command(command))
            # dump(msg)
        self.socket.send_multipart(msg)


    def reply(self, msg: bytes):
        """Format and send reply to client"""
        # assert self.expect_reply is not False
        assert self.reply_to is not None

        if msg is None:
            msg = []
        elif not isinstance(msg, list):
            msg = [msg]
        # Creating W_REPLY message consisting of:
        # Frame 3 - Client address (envelope stack)
        # Frame 4 - Empty frame (envelope delimiter)
        # Frame 5 - Reply body
        reply = [self.reply_to, b''] + msg
        self.send_to_broker(MDP.W_REPLY, msg=reply)

    def recv(self):
        """waits for next request from broker"""

        # self.expect_reply = True

        while True:
            # Poll socket for a reply, with timeout
            try:
                items = self.poller.poll(self.timeout)
            except KeyboardInterrupt:
                break  # Interrupted


            if items:
                msg = self.socket.recv_multipart()

                self.liveness = self.HEARTBEAT_LIVENESS

                assert len(msg) >= 3
                assert b'' == msg.pop(0)            # Frame 0 - empty frame
                assert MDP.W_WORKER == msg.pop(0)   # Frame 1 - header
                command = msg.pop(0)                # Frame 2 - one byte, representing type of Command


                if command == MDP.W_REQUEST:
                    if self.verbose:
                        logging.info("I: received W_REQUEST from broker: ")

                    self.reply_to = msg.pop(0)      # Frame 3 - Client address (envelope stack)
                    assert b'' == msg.pop(0)        # Frame 4 - Empty frame (envelope delimiter)
                    return msg                      # Frame 5 - Request body

                elif command == MDP.W_HEARTBEAT:
                    pass  # Do nothing for heartbeats

                elif command == MDP.W_DISCONNECT:
                    self.reconnect_to_broker()

                else:
                    logging.error("E: invalid input message: ")
                    dump(msg)

            else:
                self.liveness -= 1
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
        return None


    def destroy(self):
        # context.destroy depends on pyzmq >= 2.1.10
        self.ctx.destroy(0)
