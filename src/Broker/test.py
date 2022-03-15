import heapq
import logging
import random
import struct
import sys
import time
import weakref

import zmq
import mmh3

log = logging.getLogger(__name__)


def hash64(data):
    return mmh3.hash_bytes(data)[:8]


class Consumer(object):
    def __init__(self, addr):
        self.addr = addr
        self.topics = set()
        ctx = zmq.Context()
        self.sock = ctx.socket(zmq.DEALER)
        self.sock.connect(addr)
        self.poller = zmq.Poller()
        self.poller.register(self.sock, zmq.POLLIN)

    def _send(self, *frames):
        self.sock.send('', zmq.SNDMORE)
        self.sock.send_multipart(frames)

    def _send_all_subs(self):
        log.info("Sending all subscriptions")
        for t in self.topics:
            self._send('SUB', hash64(t))

    def subscribe(self, topic):
        h = hash64(topic)
        log.info("Subscribe: %s (%r)", topic, h)
        if topic in self.topics:
            log.info("Topic already subscribed: %s", topic)
            return
        self.topics.add(topic)
        self._send('SUB', h)

    def unsubscribe(self, topic):
        h = hash64(topic)
        log.info("Unsubscribe: %s (%r)", topic, h)
        if topic not in self.topics:
            log.info("Topic not subscribed: %s", topic)
            return
        self._send('UNSUB', h)

    def ready(self):
        log.info("Ready")
        self._send('READY')

    def recv(self, timeout=2000):
        poll = self.poller.poll(timeout)
        if not poll:
            self.ready()
            return
        msg = self.sock.recv_multipart()
        _, cmd = msg[:2]
        if cmd == 'RESET':   # Publisher wants all subscriptions
            log.info("Reset")
            self._send_all_subs()
            return None
        return msg


class Subscriber(object):
    def __init__(self, sid, ttl=7):
        self.sid = sid
        self.ttl = ttl
        self.topics = set()
        self.ready()

    def __repr__(self):
        return '<Subscriber %r expires=%.2f topics=%r' % (self.sid, self._expires - time.time(), self.topics)

    def __hash__(self):
        return hash(self.sid)

    # def __cmp__(self, other):
    #     return cmp(self.ttl, other.ttl)

    @property
    def expired(self):
        return time.time() >= self._expires

    def ready(self):
        self._expires = time.time() + self.ttl



class Publisher(object):

    def __init__(self, addr):
        self.addr = addr
        self.topics = {}   # topic -> set(sid)
        self.subscribers = weakref.WeakValueDictionary() # sid -> Subscriber
        self.expiry = []
        self.ctx = zmq.Context()
        self.sock = self.ctx.socket(zmq.ROUTER)
        self.sock.bind(self.addr)
        self.poller = zmq.Poller()
        self.poller.register(self.sock, zmq.POLLIN)

    def _subscribe(self, sid, topic):
        log.info("Subscribe: %r -> %r", sid, topic)
        try:
            sub = self.subscribers[sid]
        except KeyError:
            sub = Subscriber(sid)
            heapq.heappush(self.expiry, sub)
            self.subscribers[sid] = sub
        sub.topics.add(topic)
        sub.ready()
        self.topics.setdefault(topic, set()).add(sid)

    def _debug(self):
        log.debug("Subscribers: %r", self.expiry)

    def _expire(self):
        if not self.expiry:
            return
        oldest = heapq.heappop(self.expiry)

        if not oldest.expired:
            heapq.heappush(self.expiry, oldest)
            return

        # FIXME: Remove all traces of the sub here...
        log.info("Expired: %r", oldest)
        self._expire()

    def _unsubscribe(self, sid, topic):
        log.info("Unsubscribe: %r -> %r", sid, topic)
        try:
            subs = self.topics[topic]
            subs.discard(sid)
            if not subs:
                log.debug("No more subscribers to topic: %r", topic)
                self.topics.pop(topic)
            sub = self.subscribers[sid]
            sub.topics.remove(topic)
            if not sub.topics:
                log.debug("No more topics for subscriber: %r", sid)
                self.subscribers.pop(sid)
        except KeyError:
            log.error("Error unsubscribing Topic: %r @ SID: %r", topic, sid)

    def _ready(self, sid):
        log.info("Ready: %r", sid)
        sub = self.subscribers.get(sid, None)
        if sub:
            sub.ready()
        else:
            log.info("Reset: %r", sid)
            self.sock.send_multipart([sid, '', 'RESET'])  # Request all subscriptions to be re-sent
        self._debug()

    def publish(self, topic, *payload):
        log.info("Publishing a message: topic=%r  payload=%r", topic, payload)
        h = hash64(topic)
        msg = [zmq.Message(m) for m in ('', 'PUB', h) + payload]

        for dest in self.topics.get(h, []):
            self.sock.send(dest, zmq.SNDMORE)
            self.sock.send_multipart(msg, copy=False, track=False)

    def start(self):
        t = 0
        while True:
            if time.time() > t:
                topic = random.choice(["foo", "bar", "baz", "quux"])
                self.publish(topic, "howdy %s" % topic)
                t = time.time() + 1.5
            poll = self.poller.poll(1000)
            if not poll:
                log.debug("Idle...")
                self._debug()
                self._expire()
                continue
            self._expire()
            msg = self.sock.recv_multipart()
            sid, _, cmd = msg[:3]
            payload = msg[3:]
            if cmd == 'SUB':
                self._subscribe(sid, payload[0])
            elif cmd == 'UNSUB':
                self._unsubscribe(sid, payload[0])
            elif cmd == 'READY':
                self._ready(sid)
            else:
                log.error("Fscked command: %s", cmd)


def run_consumer():
    c = Consumer("tcp://localhost:9292")
    c.subscribe("foo")
    c.subscribe("bar")
    c.unsubscribe("bar")
    c.subscribe("baz")
    while True:
        msg = c.recv()
        if msg:
            log.info("Recv: %r", msg)


def run_publisher():
    c = Publisher("tcp://*:9292")
    c.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    cmd = sys.argv[1]
    if cmd == 'pub':
        run_publisher()
    else:
        run_consumer()
