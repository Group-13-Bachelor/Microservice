from flaskblog.models import Post
from datetime import datetime

# Local
from flaskblog import client
from common.MDP import EVENTS
from common import utils


def save_new_post(post: Post):
	msg = {
		"title": post.title,
		"content": post.content,
		"user_id": post.user_id,
		"username": post.username
	}
	client.send(EVENTS.post_saved, utils.encode_msg(msg))
	return True


def get_all_posts():
	message_bytes = client.request(EVENTS.get_all_post, "".encode('utf-8'))
	assert message_bytes is not None
	msg = utils.msg_to_dict(message_bytes)

	posts = []
	for post in msg:
		posts.append(
			Post(
				id=post["id"],
				title=post["title"],
				date_posted=datetime.strptime(post["date_posted"], '%a, %d %b %Y %X '),
				content=post["content"],
				user_id=post["user_id"],
				username=post["username"]
			)
		)
	print(f"{posts}")
	return posts


def get_post_id(post_id: int):
	message_bytes = client.request(EVENTS.get_post, str(post_id).encode('utf-8'))
	msg = utils.msg_to_dict(message_bytes)

	post = Post(
		id=msg["id"],
		title=msg["title"],
		date_posted=datetime.strptime(msg["date_posted"], '%a, %d %b %Y %X '),
		content=msg["content"],
		user_id=msg["user_id"],
		username=msg["username"]
	)
	return post


def update_post(post, new_post):
	msg = {
		"id": post.id,
		"title": new_post["title"],
		"content": new_post["content"],
		"user_id": post.user_id,
		"username": post.username
	}
	client.send(EVENTS.post_updated, utils.encode_msg(msg))


def delete_post(post_id):
	msg = {
		"id": post_id
	}
	client.send(EVENTS.post_deleted, utils.encode_msg(msg))
