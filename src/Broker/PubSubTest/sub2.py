import zmq
from datetime import datetime


xpub_addr = 'tcp://127.0.0.1:5555'
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect(xpub_addr)
socket.setsockopt_string(zmq.SUBSCRIBE, "event2")

while True:
    if socket.poll(timeout=1000):
        message = socket.recv_multipart()
        print(f"{message} - {datetime.now()}")

