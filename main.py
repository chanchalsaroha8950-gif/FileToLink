import asyncio
import logging
from multiprocessing import Process

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application, CallbackQueryHandler, ChatJoinRequestHandler, CommandHandler, MessageHandler, filters

from config import BOT_TOKEN, BOT_TOKEN1, BROADCAST_CLEANUP_INTERVAL_MINUTES, CLEANUP_INTERVAL_MINUTES
from database.db import init_db
from handlers.admin import admin_callback_handler, admin_text_handler, cancel_admin_command, admin_panel
from handlers.channel import add_channel_command, channel_join_request_handler, remove_channel_callback
from handlers.deliver import deliver_callback_handler
from handlers.start import start_handler
from handlers.upload import copy_link_callback_handler, upload_handler
from scheduler.cleanup import cleanup_broadcasts, cleanup_expired_files
from utils.helpers import ADMIN_STATE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def post_init(app: Application) -> None:
    scheduler = AsyncIOScheduler(event_loop=asyncio.get_running_loop())
    scheduler.add_job(cleanup_expired_files, "interval", minutes=CLEANUP_INTERVAL_MINUTES, kwargs={"bot": app.bot})
    scheduler.add_job(cleanup_broadcasts, "interval", minutes=BROADCAST_CLEANUP_INTERVAL_MINUTES)
    scheduler.start()
    app.bot_data["scheduler"] = scheduler
    logger.info("Scheduler initialized")


async def post_stop(app: Application) -> None:
    scheduler = app.bot_data.get("scheduler")
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


def build_application(bot_token: str, bot_role: str) -> Application:
    application = Application.builder().token(bot_token).build()
    application.bot_data["role"] = bot_role

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(ChatJoinRequestHandler(channel_join_request_handler))
    application.add_handler(CallbackQueryHandler(deliver_callback_handler, pattern=r"^check_"))

    if bot_role == "primary":
        application.add_handler(CommandHandler("admin", admin_panel))
        application.add_handler(CommandHandler("addchannel", add_channel_command))
        application.add_handler(CommandHandler("cancel", cancel_admin_command))

        application.add_handler(
            CallbackQueryHandler(
                admin_callback_handler,
                pattern=r"^(stats|broadcast|add_channel|remove_channel|channel_list)$",
            )
        )
        application.add_handler(
            CallbackQueryHandler(remove_channel_callback, pattern=r"^remove_"),
        )
        application.add_handler(
            CallbackQueryHandler(copy_link_callback_handler, pattern=r"^copy_"),
        )

        media_filter = filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO
        application.add_handler(MessageHandler(media_filter, upload_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text_handler))

        application.post_init = post_init
        application.post_stop = post_stop

    return application


def run_bot(bot_token: str, bot_role: str) -> None:
    if bot_token == "YOUR_BOT_TOKEN_HERE":
        logger.warning("%s token is not configured. Set it in .env before running.", bot_role)

    init_db()
    logger.info("Starting bot in %s mode", bot_role)
    application = build_application(bot_token, bot_role)
    application.run_polling()


def run() -> None:
    secondary_process: Process | None = None
    try:
        if BOT_TOKEN1 and BOT_TOKEN1 != BOT_TOKEN:
            secondary_process = Process(target=run_bot, args=(BOT_TOKEN1, "secondary"), daemon=True)
            secondary_process.start()
        elif BOT_TOKEN1 == BOT_TOKEN:
            logger.warning("BOT_TOKEN1 matches BOT_TOKEN. Secondary bot will not be started.")

        run_bot(BOT_TOKEN, "primary")
    finally:
        if secondary_process and secondary_process.is_alive():
            secondary_process.terminate()
            secondary_process.join(timeout=5)


if __name__ == "__main__":
    run()
