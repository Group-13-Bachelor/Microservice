from binascii import hexlify
import json
import zmq


# Local
from common import MDP


def dump(msg_or_socket):
	"""Receives all message parts from socket, printing each frame neatly"""
	if isinstance(msg_or_socket, zmq.Socket):
		# it's a socket, call on current message
		msg = msg_or_socket.recv_multipart()
	else:
		msg = msg_or_socket
	print("----------------------------------------")
	for part in msg:
		command = MDP.bytes_commands.get(part)
		if command is not None:
			print(f"[%03d] {command}" % len(part))
		else:
			try:
				print(f"[%03d] {part.decode('ascii')}" % len(part))
			except UnicodeDecodeError:
				print(f"[%03d] 0x{hexlify(part).decode('ascii')}" % len(part))
	print("----------------------------------------")


def bytes_to_command(msg):
	command = MDP.bytes_commands.get(msg)
	if command is not None:
		return command
	else:
		return msg


def encode_msg(msg) -> bytes:
	"""Encodes message to bytes
	Excepts string like objects"""
	# msg_ascii = str(msg).encode('ascii')
	# return base64.b64encode(msg_ascii)
	return str(msg).encode('ascii')


def msg_to_dict(msg: bytes) -> dict:
	# message_decoded = base64.b64decode(msg).decode('utf8')
	message_decoded = msg.decode('ascii')
	json_acceptable_string = message_decoded.replace("'", "\"")
	message = json.loads(json_acceptable_string)
	# print(f"message: {message}")
	return message
