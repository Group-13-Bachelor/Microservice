import zmq
from datetime import datetime

xpub_addr = 'tcp://127.0.0.1:5555'
context = zmq.Context()
subscriberSocket = context.socket(zmq.SUB)
subscriberSocket.connect(xpub_addr)
subscriberSocket.setsockopt_string(zmq.SUBSCRIBE, "get_all_posts")

while True:
    if subscriberSocket.poll(timeout=1000):
        message = subscriberSocket.recv_multipart()
        print(f"{message} - {datetime.now()}")



        if message[1] == b'event1' or message[1] == b'event2':
            subscriberSocket.setsockopt_string(zmq.SUBSCRIBE, message[1].decode('UTF-8'))
            print(f"\t blarg")
