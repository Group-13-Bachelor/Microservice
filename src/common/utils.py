from binascii import hexlify
from typing import Optional
import json
import base64
import zmq


# Local
from common import MDP


def dump(msg_or_socket, log=None):
	"""Receives all message parts from socket, printing each frame neatly"""
	if log is None:
		log = print

	if isinstance(msg_or_socket, zmq.Socket):
		# it's a socket, call on current message
		msg = msg_or_socket.recv_multipart()
	else:
		msg = msg_or_socket
	log("----------------------------------------")
	for part in msg:
		command = MDP.bytes_commands.get(part)
		if command is not None:
			log(f"[%03d] {command}" % len(part))
		else:
			try:
				log(f"[%03d] {part.decode('ascii')}" % len(part))
			except UnicodeDecodeError:
				log(f"[%03d] 0x{hexlify(part).decode('ascii')}" % len(part))
	log("----------------------------------------")


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
	print(f"message: {message}")
	return message
