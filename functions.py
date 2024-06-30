from telegram import Update

from models import User


def create_user(update: Update) -> User:
    user_data = update.effective_user.to_dict()
    return User(
        user_data["id"],
        user_data.get("first_name"),
        user_data.get("last_name"),
        user_data["username"],
        user_data["language_code"],
        user_data["is_bot"],
    )
