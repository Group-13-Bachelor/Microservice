from typing import List
from datetime import datetime

# Local
from flaskblog import db
from flaskblog.models import User, Post
from flaskblog import producer
from common.MDP import EVENTS
from common import utils


def register_user(user: User):
	# Saves user to "cache"
	db.session.add(user)
	db.session.commit()

	msg = {
		"username": user.username,
		"email": user.email,
		"password": user.password,
		"image_file": user.image_file  # This will be None if user is not committed
	}
	producer.send(EVENTS.create_user, utils.encode_msg(msg))  # TODO This should be a command to check if we can create the user




def update_user(current_user):
	user = {
		"id": current_user.id,
		"username": current_user.username,
		"email": current_user.email
	}

	producer.send(EVENTS.update_user, utils.encode_msg(user))


def get_user(**kwargs):
	"""
	    Keyword Args:
	        username (string): Users username
	        id (int): Users ID
	        email (string): Users Email
	"""
	data = None
	for key, value in kwargs.items():
		data = {key: value}

	if data is not None:  # TODO: improve this
		# Super duper cache
		for key, value in data.items():
			user = User.query.filter_by(**{key: value}).first()
			if user:
				return user

		message_bytes = producer.request(EVENTS.get_user, utils.encode_msg(data))
		msg = utils.msg_to_dict(message_bytes)

		user = User(
			id=msg["id"],
			username=msg["username"],
			email=msg["email"],
			image_file="default.jpg",
			password=msg["password"]
		)
		db.session.add(user)
		db.session.commit()
		return user


def get_users_posts(user_id: int) -> List[dict]:
	message_bytes = producer.request(EVENTS.get_post_by_user, str(user_id).encode('ascii'))
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

	return posts
