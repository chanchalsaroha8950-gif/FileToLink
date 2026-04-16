import re
from typing import Optional

from telegram import Message, Update

ADMIN_STATE: dict[int, str] = {}


def is_admin(user_id: int, admin_id: int) -> bool:
    return user_id == admin_id


def get_target_message(update: Update) -> Optional[Message]:
    if update.message:
        return update.message
    if update.callback_query and update.callback_query.message:
        return update.callback_query.message
    return None


def normalize_channel_username(channel_username: str) -> str:
    username = channel_username.strip()
    if username.startswith("https://t.me/"):
        username = "@" + username.split("https://t.me/", 1)[1].strip("/")
    if not username.startswith("@"):
        username = "@" + username
    return username


def parse_quoted_parts(text: str) -> list[str]:
    return re.findall(r'"([^"]*)"', text, re.DOTALL)
