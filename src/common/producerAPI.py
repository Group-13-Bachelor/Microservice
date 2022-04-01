"""Majordomo Protocol Client API, Python version.
Implements the MDP/Worker spec at http:#rfc.zeromq.org/spec:7.
Author: Min RK <benjaminrk@gmail.com>
Based on Java example by Arkadiusz Orzechowski
"""

import logging
import zmq

from common import MDP
from common.utils import dump


class Producer(object):
    """Majordomo Protocol Client API, Python version.
      Implements the MDP/Worker spec at http:#rfc.zeromq.org/spec:7.
    """
    broker = None
    ctx = None
    client = None
    poller = None
    timeout = 5000  # in milliseconds
    verbose = False
    expect_reply = False

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
        if self.client:
            self.poller.unregister(self.client)
            self.client.close()
        self.client = self.ctx.socket(zmq.DEALER)
        self.client.linger = 0
        self.client.connect(self.broker)
        self.poller.register(self.client, zmq.POLLIN)

        if self.verbose:
            logging.info("I: connecting to broker at %s...", self.broker)

    def destroy(self):
        self.ctx.destroy(0)

    def request(self, service, request) -> bytes:
        """Send message to broker and waits for response"""
        self.send(service, request, response=True)
        return self.recv()

    def send(self, service, request, response=False):
        """Send and forget message to broker"""
        self.expect_reply = response
        if not isinstance(request, list):
            request = [request]

        # Prefix request with protocol frames:
        # Frame 0 - empty (REQ emulation since DEALER dos not append this)
        # Frame 1 - "MDPCxy" (six bytes, MDP/Client x.y)
        # Frame 2 - Service name
        # Frame 3 - Request body
        msg = [b'', MDP.P_PRODUCER, service] + request
        if self.verbose:
            logging.info(f"I: send event {service}, msg: {msg}")
        self.client.send_multipart(msg)

    def recv(self) -> bytes:
        """Returns the reply message or None if there was no reply."""
        try:
            items = self.poller.poll(self.timeout)
        except KeyboardInterrupt:
            return  # interrupted

        if items and self.expect_reply:
            self.expect_reply = False

            msg = self.client.recv_multipart()
            if self.verbose:
                logging.info("I: received reply:")
                dump(msg)

            # Not trying to handle errors, just asserting noisily
            assert len(msg) >= 4
            empty = msg.pop(0)                  # Frame 0 - empty frame
            assert MDP.P_PRODUCER == msg.pop(0)   # Frame 1 - “MDPC01” (six bytes, representing MDP/Client v0.1)
            service = msg.pop(0)                # Frame 2 - Service name

            if len(msg) == 1:
                return msg.pop(0)               # Frame 4 - message body
            else:
                return msg                      # Frame 4 - message body
        else:
            logging.warning(f"W: Unexpected request: {items}")
