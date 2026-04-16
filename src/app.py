import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from src import database
from src.config import BOT_TOKEN, BROADCAST_CLEANUP_INTERVAL_MINUTES, CLEANUP_INTERVAL_MINUTES
from src.handlers import FileBotHandlers
from src.scheduler import cleanup_broadcasts, cleanup_expired_files

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def post_init(app: Application) -> None:
    """Initialize scheduler when app starts."""
    loop = asyncio.get_event_loop()
    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.add_job(cleanup_expired_files, "interval", minutes=CLEANUP_INTERVAL_MINUTES)
    scheduler.add_job(cleanup_broadcasts, "interval", minutes=BROADCAST_CLEANUP_INTERVAL_MINUTES)
    scheduler.start()
    app.bot_data["scheduler"] = scheduler
    logger.info("Scheduler initialized and started")


async def post_stop(app: Application) -> None:
    """Shut down scheduler when app stops."""
    if "scheduler" in app.bot_data:
        app.bot_data["scheduler"].shutdown()
        logger.info("Scheduler shut down")


def main() -> None:
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.warning("BOT_TOKEN is not configured. Set BOT_TOKEN env var before running the bot.")

    database.init_db()

    app = Application.builder().token(BOT_TOKEN).build()
    handlers = FileBotHandlers()

    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("admin", handlers.admin_panel))
    app.add_handler(CommandHandler("addchannel", handlers.add_channel_command))

    app.add_handler(CallbackQueryHandler(handlers.button_callback, pattern=r"^check_"))
    app.add_handler(
        CallbackQueryHandler(
            handlers.admin_callback,
            pattern=r"^(stats|broadcast|add_channel|remove_channel|channel_list|remove_)",
        )
    )

    media_filter = filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO
    app.add_handler(MessageHandler(media_filter, handlers.handle_file))

    app.post_init = post_init
    app.post_stop = post_stop

    app.run_polling()


def run() -> None:
    main()
