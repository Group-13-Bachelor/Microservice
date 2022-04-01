"""Majordomo Protocol definitions"""
#  This is the version of MDP/Client we implement
P_PRODUCER = b"MDPC01"

#  This is the version of MDP/Worker we implement
C_CONSUMER = b"MDPW01"


""" MDP/Server commands, as strings
All start with:
	Frame 0 - Client/worker peer identity added by ROUTER socket
	Frame 1 - Empty frame, de
	Frame 2 - header, C_CLIENT or W_WORKER
W_READY
	Frame 3 - The command
	Frame 4 - Event name
W_REQUEST
	Frame 3 - Client address (envelope stack)
	Frame 4 - Empty frame (envelope delimiter)
	Frame 5 - Request body
	Frame 5 - Event name	
W_REPLY
	Frame 3 - The command
	Frame 4 - Client identity added by ROUTER socket
	Frame 5 - empty frame
	Frame 6 - Reply message to client
	Frame 7 - Event name

W_HEARTBEAT and W_DISCONNECT has no extra frames"""
W_READY         =   b"\001"
W_REQUEST       =   b"\002"
W_REPLY         =   b"\003"
W_HEARTBEAT     =   b"\004"
W_DISCONNECT    =   b"\005"
W_GROUP			=   b"\006"


bytes_commands = {
	b'\001': "W_READY",
	b'\002': "W_REQUEST",
	b'\003': "W_REPLY",
	b'\004': "W_HEARTBEAT",
	b'\005': "W_DISCONNECT"
}


class EVENTS:
	"""Constants for event names"""
	save_post = b"save_post"
	post_saved = b"post_saved"
	update_post = b"update_post"
	post_updated = b"post_updated"
	censor_post = b"censor_post"
	post_deleted = b"post_deleted"
	get_post = b"get_post"
	get_all_post = b"get_all_post"

	create_user = b"create_user"
	user_created = b"user_created"
	update_user = b"update_user"
	user_updated = b"user_updated"
	censor_user = b"censor_user"
	get_user = b"get_user"
	get_post_by_user = b"get_post_by_user"


class GROUP:
	"""Constants for consumer group names"""
	user_group = b"user_group"
	post_group = b"post_group"
	filter_group = b"filter_group"




# Note, Python3 type "bytes" are essentially what Python2 "str" were,
# but now we have to explicitly mark them as such.  Type "bytes" are
# what PyZMQ expects by default.  Any user code that uses this and
# related modules may need to be updated.  Here are some guidelines:
#
# String literals that make their way into messages or used as socket
# identfiers need to become bytes:
#
#   'foo' -> b'foo'
#
# Multippart messages, originally formed as lists of strings (smsg)
# need to be washed into strings of bytes (bmsg) like:
#
#   bmsg = [one.encode('utf-8') for one in smsg]
#
# A multipart message recived can be reversed
#
#   smsg = [one.decode() for one in bmsg]
