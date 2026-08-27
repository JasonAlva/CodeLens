# pyrefly: ignore [missing-import]
from utils import format_user
# pyrefly: ignore [missing-import]
from database import save_user
# pyrefly: ignore [missing-import]
from models.user import User


def create_user(name, age):
    user = User(name, age)
    save_user(user)
    return user


def display_user(user):
    formatted = format_user(user)
    print(formatted)


def main():
    user = create_user("Jason", 20)
    display_user(user)


if __name__ == "__main__":
    main()