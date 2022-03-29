from flask_bcrypt import Bcrypt
import sys

# Local
from UserService import app, db
from UserService.model import User
from common.MDP import EVENTS, GROUP
from common import utils, serviceAPI, clientAPI


def main():
	verbose = '-v' in sys.argv
	worker = serviceAPI.Service("tcp://localhost:5555", False)
	client = clientAPI.Client("tcp://localhost:5555", False)
	register(worker)

	while True:
		value, event = worker.recv()
		print(f"event: {event}, value: {value}")
		if event == EVENTS.get_user:
			posts = get_user(utils.msg_to_dict(value))
			worker.reply(utils.encode_msg(posts))

		elif event == EVENTS.update_user:
			user = update_user(utils.msg_to_dict(value))
			client.send(EVENTS.user_updated, utils.encode_msg(user))
			worker.ready()

		elif event == EVENTS.create_user:
			user = register_user(utils.msg_to_dict(value))
			client.send(EVENTS.user_created, utils.encode_msg(user))
			worker.ready()

		elif event == EVENTS.censor_user:
			pass


def register(worker):
	worker.add_to_group(GROUP.user_group)

	worker.subscribe(EVENTS.get_user)
	worker.subscribe(EVENTS.update_user)
	worker.subscribe(EVENTS.create_user)
	worker.subscribe(EVENTS.censor_user)


def register_user(msg: dict):
	user = User(
		username=msg["username"],
		email=msg["email"],
		image_file=msg["image_file"],
		password=msg["password"])
	db.session.add(user)
	db.session.commit()

	return user_to_dict(user)


def get_user(msg: dict):
	user = None
	if "username" in msg:
		user = User.query.filter_by(username=msg["username"]).first()
	elif "id" in msg:
		user = User.query.filter_by(id=msg["id"]).first()
	elif "email" in msg:
		user = User.query.filter_by(email=msg["email"]).first()

	if user is not None:
		return user_to_dict(user)
	else:
		return 404


def update_user(msg: dict) -> dict:
	user = User.query.filter_by(id=msg["id"]).first()
	user.username = msg["username"]
	user.email = msg["email"]

	db.session.commit()

	return user_to_dict(user)


def user_to_dict(user: User) -> dict:
	return {
		"id": user.id,
		"username": user.username,
		"email": user.email,
		"image_file": user.image_file,
		"password": user.password
	}


def init_db():
	with app.app_context():
		db.drop_all()
		db.create_all()
		db.session.commit()

	bcrypt = Bcrypt()

	users = [
		User(username="user1", email="user1@email.mail", password=bcrypt.generate_password_hash("123").decode('utf-8')),
		User(username="user2", email="user2@email.mail", password=bcrypt.generate_password_hash("123").decode('utf-8')),
		User(username="user3", email="user3@email.mail", password=bcrypt.generate_password_hash("123").decode('utf-8'))
	]
	for user in users:
		db.session.add(user)
	db.session.commit()
	print("DB initialized")
	print(User.query.all())


if __name__ == '__main__':
	# init_db()
	main()
