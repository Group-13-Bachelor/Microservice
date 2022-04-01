from typing import List, Dict
import sys

# Local
from PostService import app, db
from PostService.model import Post
from common.MDP import EVENTS, GROUP
from common import utils, consumerAPI, producerAPI


def main():
	verbose = '-v' in sys.argv
	consumer = consumerAPI.Consumer("tcp://localhost:5555", False)
	producer = producerAPI.Producer("tcp://localhost:5555", True)
	register(consumer)


	while True:
		value, event = consumer.recv()
		print(f"event: {event}, value: {value}")
		if event == EVENTS.get_all_post:
			posts = get_all_posts()
			msg = utils.encode_msg(posts)
			consumer.reply(msg)

		elif event == EVENTS.get_post:
			post = get_post(value.decode('utf-8'))
			msg = utils.encode_msg(post)
			consumer.reply(msg)

		elif event == EVENTS.save_post:
			post = save_post(utils.msg_to_dict(value))
			producer.send(EVENTS.post_saved, utils.encode_msg(post))
			consumer.ready()

		elif event == EVENTS.update_post:
			post = update_post(utils.msg_to_dict(value))
			producer.send(EVENTS.post_updated, utils.encode_msg(post))
			consumer.ready()

		elif event == EVENTS.post_deleted:
			delete_post(utils.msg_to_dict(value))
			consumer.ready()

		elif event == EVENTS.censor_post:
			update_post(utils.msg_to_dict(value))
			consumer.ready()

		elif event == EVENTS.get_post_by_user:
			posts = get_posts_by_user(value.decode('utf-8'))
			msg = utils.encode_msg(posts)
			consumer.reply(msg)

		elif event == EVENTS.user_updated:
			update_user(utils.msg_to_dict(value))
			consumer.ready()


def register(worker):
	worker.add_to_group(GROUP.post_group)

	worker.subscribe(EVENTS.get_all_post)
	worker.subscribe(EVENTS.get_post)
	worker.subscribe(EVENTS.save_post)
	worker.subscribe(EVENTS.update_post)
	worker.subscribe(EVENTS.post_deleted)
	worker.subscribe(EVENTS.censor_post)

	worker.subscribe(EVENTS.get_post_by_user)
	worker.subscribe(EVENTS.user_updated)


def get_all_posts() -> List[dict]:
	posts = []
	for post in Post.query.all():
		posts.append(post_to_dict(post))
	return posts


def get_post(post_id: int) -> dict:
	print(f"ID: {post_id}")
	post = Post.query.get(post_id)
	return post_to_dict(post)


def save_post(msg: dict):
	post = Post(
		title=msg["title"],
		content=msg["content"],
		user_id=msg["user_id"],
		username=msg["username"])
	db.session.add(post)
	db.session.commit()
	return post_to_dict(post)




def get_posts_by_user(user_id: int) -> List[dict]:
	posts = []
	for post in Post.query.filter_by(user_id=user_id).all():
		posts.append(post_to_dict(post))
	return posts



def update_post(msg: dict) -> dict:
	post = Post.query.get(msg["id"])
	post.title = msg["title"]
	post.content = msg["content"]

	db.session.commit()

	return post_to_dict(post)


def delete_post(msg):
	post = Post.query.get(msg["id"])

	db.session.delete(post)
	db.session.commit()


def update_user(msg: dict):
	posts = Post.query.filter_by(user_id=msg["id"]).all()
	for post in posts:
		post.username = msg["username"]

	db.session.commit()


def post_to_dict(post: Post) -> Dict[str, str]:
	return {
		"id": post.id,
		"title": post.title,
		"date_posted": post.date_posted.strftime('%a, %d %b %Y %X %Z'),
		"content": post.content,
		"user_id": post.user_id,
		"username": post.username
	}


def init_db():
	with app.app_context():
		db.drop_all()
		db.create_all()
		db.session.commit()

	posts = [
		Post(title="title 1", content="Content 1", user_id=1, username="user1"),
		Post(title="title 2", content="Content 2", user_id=2, username="user2"),
		Post(title="title 3", content="Content 31", user_id=3, username="user3"),
		Post(title="title 4", content="Content 32", user_id=3, username="user3")
	]

	for post in posts:
		db.session.add(post)
	db.session.commit()
	print("DB initialized:")
	print(Post.query.all())


if __name__ == '__main__':
	# init_db()
	main()
