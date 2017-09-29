from app import db
from app.models import User
import argparse


def add_user(username, password):
    user = User(username=username)
    user.hash_password(password)
    db.session.add(user)
    db.session.commit()


def verify_password(username, password):
    user = User.query.filter_by(username = username).first()
    if not user or not user.verify_password(password):
        return False
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create user')
    parser.add_argument(
        '-u', '--user-name',
        type=str, help='User name', required=True)
    parser.add_argument(
        '-p', '--password',
        type=str, help='User name', required=True)
    args = parser.parse_args()
    add_user(args.user_name, args.password)
    assert(verify_password(args.user_name, args.password))
