import asyncio
from datetime import datetime, timedelta

from telegram.error import RetryAfter

from database.db import add_broadcast_record, list_users


async def broadcast_message(source_message, context) -> tuple[int, int]:
    users = list_users()
    delete_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    success = 0

    for user_id, _, _ in users:
        try:
            sent = await source_message.copy(user_id)
            add_broadcast_record(sent.id, user_id, delete_at)
            success += 1
        except RetryAfter as exc:
            await asyncio.sleep(exc.value)
        except Exception:
            pass

    return success, len(users)
