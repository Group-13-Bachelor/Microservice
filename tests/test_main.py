
import unittest
from threading import Thread
import time

from src.Broker.broker import MessageBroker
from src.common.consumerAPI import Consumer
from src.common.producerAPI import Producer


class TestBroker(unittest.TestCase):
    """Test cased for broker"""


    def setUp(self) -> None:
        self.broker = MessageBroker()
        self.broker.bind("tcp://*:5555")
        self.brokerThread = Thread(target=self.broker.mediate)
        self.brokerThread.start()

        self.consumer = Consumer("tcp://localhost:5555", False)
        self.producer = Producer("tcp://localhost:5555", False)

        self.event = b"test"

    def tearDown(self) -> None:
        # Stop broker
        self.broker.mediating = False
        self.broker.destroy()

        self.brokerThread.join()

        print(self.brokerThread.is_alive())

        # Stop consumer and producer
        self.consumer.destroy()
        self.producer.destroy()


    def test_subscription(self):
        self.consumer.subscribe(self.event)

        # Waits for subscription to be registered in thread
        while len(self.broker.Events.keys()) == 0:  # TODO Add timeout
            time.sleep(0.5)

        self.assertTrue(self.event in self.broker.Events.keys())


    def test_event(self):
        msg = b"test"
        self.producer.request(self.event, msg)

        value, event = self.consumer.recv()  # TODO Move to its own Thread

        self.assertTrue(value == msg)
        self.assertTrue(event == self.event)



if __name__ == '__main__':
    unittest.main()     # This allows for infile testing with pytest
