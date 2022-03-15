import zmq

xpub_addr = 'tcp://127.0.0.1:5555'
xsub_addr = 'tcp://127.0.0.1:5556'
context = zmq.Context()

# create XPUB
xpub_socket = context.socket(zmq.XPUB)
xpub_socket.bind(xpub_addr)
xsub_socket = context.socket(zmq.XSUB)
xsub_socket.bind(xsub_addr)

frontend = context.socket(zmq.ROUTER)
backend = context.socket(zmq.DEALER)
frontend.bind("tcp://127.0.0.1:5559")
backend.bind("tcp://127.0.0.1:5560")

# create poller
poller = zmq.Poller()
poller.register(xpub_socket, zmq.POLLIN)
poller.register(xsub_socket, zmq.POLLIN)

poller.register(frontend, zmq.POLLIN)
poller.register(backend, zmq.POLLIN)


while True:
	# get event
	event = dict(poller.poll(1000))

	if xpub_socket in event:
		message = xpub_socket.recv_multipart()
		print("[BROKER] xpub_socket recv message: %r" % message)
		xsub_socket.send_multipart(message)
	if xsub_socket in event:
		message = xsub_socket.recv_multipart()
		print("[BROKER] xsub_socket recv message: %r" % message)
		xpub_socket.send_multipart(message)

	if frontend in event:
		message = frontend.recv_multipart()
		print("[BROKER] frontend_socket recv message: %r" % message)
		backend.send_multipart(message)

	if backend in event:
		message = backend.recv_multipart()
		print("[BROKER] backend_socket recv message: %r" % message)
		frontend.send_multipart(message)