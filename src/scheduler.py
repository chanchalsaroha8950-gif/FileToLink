import logging
import os

from src import database

logger = logging.getLogger(__name__)


async def cleanup_expired_files() -> None:
    expired_files = database.get_expired_files()

    for file_id, file_path in expired_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as exc:
            logger.error("Failed to remove file %s: %s", file_path, exc)
        finally:
            database.delete_file_record(file_id)


async def cleanup_broadcasts() -> None:
    # Placeholder for future broadcast cleanup logic.
    return
