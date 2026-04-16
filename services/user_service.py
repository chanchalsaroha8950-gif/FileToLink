from database.db import save_user as db_save_user


async def save_user(user_id: int, username: str | None, first_name: str | None) -> None:
    db_save_user(user_id, username, first_name)
