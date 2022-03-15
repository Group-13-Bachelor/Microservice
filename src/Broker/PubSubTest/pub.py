import zmq

xsub_addr = 'tcp://127.0.0.1:5556'
context = zmq.Context()
event1_socket = context.socket(zmq.PUB)
event1_socket.connect(xsub_addr)
topic = "event1".encode('utf-8')

while True:
    topic = input('input topic:').encode('utf-8')
    message = input('input message:').encode('utf-8')
    event1_socket.send_multipart([topic, message])
    print(f"Sending:{message}")