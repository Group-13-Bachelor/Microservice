from common import MDP, utils, serviceAPI, clientAPI



def main():
	worker = serviceAPI.Service("tcp://localhost:5555", False)
	worker.subscribe(MDP.post_updated)
	worker.subscribe(MDP.post_saved)
	worker.subscribe(MDP.user_updated)
	worker.subscribe(MDP.user_created)


	while True:
		value, event = worker.recv()
		print(f"event: {event}, value: {value}")
		if event == MDP.post_updated:
			post = utils.msg_to_dict(value)
			if post["content"] == "naughty":
				print("not nice")
		elif event == MDP.post_saved:
			pass
		elif event == MDP.user_updated:
			pass
		elif event == MDP.user_created:
			pass


if __name__ == '__main__':
	main()
