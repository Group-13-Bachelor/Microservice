from typing import List

from common.MDP import EVENTS, GROUP
from common import utils, producerAPI, consumerAPI



class Filter:
	def __init__(self, broker: str, words: List[str], verbose=False):
		self.nono_words = words
		self.broker = broker
		self.worker = None
		self.client = None
		self.verbose = verbose

		self.setup()

	def setup(self):
		self.worker = consumerAPI.Consumer(self.broker, self.verbose)
		self.client = producerAPI.Producer(self.broker, self.verbose)

		self.worker.add_to_group(GROUP.filter_group)

		self.worker.subscribe(EVENTS.post_updated)
		self.worker.subscribe(EVENTS.post_saved)
		self.worker.subscribe(EVENTS.user_updated)
		self.worker.subscribe(EVENTS.user_created)


	def work(self):
		while True:
			value, event = self.worker.recv()
			print(f"event: {event}, value: {value}")
			if event == EVENTS.post_updated:
				post = utils.msg_to_dict(value)
				self.filter_post_content(post)

			elif event == EVENTS.post_saved:
				post = utils.msg_to_dict(value)
				self.filter_post_content(post)

			elif event == EVENTS.user_updated:
				pass

			elif event == EVENTS.user_created:
				pass

	def filter_post_content(self, post):
		content = post["content"]
		words = [x for x in self.nono_words if x in content]
		for w in words:
			content = content.replace(w, "*" * len(w))
		if words:
			post["content"] = content
			self.client.send(EVENTS.censor_post, utils.encode_msg(post))

		self.worker.ready()


if __name__ == '__main__':
	f = Filter("tcp://localhost:5555", ["naughty", "Putin", "spam"])
	f.work()
