# pyrefly: ignore [missing-import]
from models.user import User


class Database:
    def __init__(self):
        self.users = []

    def add_user(self, user):
        self.users.append(user)

    def get_users(self):
        return self.users


def save_user(user):
    database = Database()
    database.add_user(user)
    return True