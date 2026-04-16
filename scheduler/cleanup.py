import os

from database.db import delete_broadcast_record, delete_file_record, get_expired_broadcasts, get_expired_files


async def cleanup_expired_files(bot=None) -> None:
    for file_id, file_path, storage_chat_id, storage_message_id in get_expired_files():
        try:
            if storage_chat_id and storage_message_id and bot:
                await bot.delete_message(chat_id=storage_chat_id, message_id=storage_message_id)
            elif file_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass
        finally:
            delete_file_record(file_id)


async def cleanup_broadcasts() -> None:
    for message_id, chat_id in get_expired_broadcasts():
        delete_broadcast_record(message_id, chat_id)
