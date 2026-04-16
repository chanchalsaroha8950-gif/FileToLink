import uuid
from html import escape

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import ADMIN_ID, BOT_TOKEN1, FILE_EXPIRY_MINUTES, NEVER_EXPIRE_LINKS, STORAGE_CHANNEL_ID
from database.db import save_user
from services.file_service import build_share_link, store_uploaded_file
from utils.helpers import get_target_message


async def _get_share_bot_username() -> str:
    """Get the username of the bot to use for share links (BOT_TOKEN1 if available, else current bot)."""
    if BOT_TOKEN1:
        try:
            share_bot = Bot(token=BOT_TOKEN1)
            me = await share_bot.get_me()
            return me.username or ""
        except Exception:
            # Fallback to dynamic username if BOT_TOKEN1 fails
            return ""
    return ""


async def copy_link_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data:
        return

    if not query.data.startswith("copy_"):
        return

    file_id = query.data.split("_", 1)[1]
    bot_username = await _get_share_bot_username()
    if not bot_username:
        bot_username = (await context.bot.get_me()).username or ""

    link = build_share_link(bot_username, file_id)
    await query.answer(text=link, show_alert=True)


async def upload_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = get_target_message(update)
    if not message or not update.effective_user:
        return

    if update.effective_user.id != ADMIN_ID:
        await message.reply_text("❌ Only admin can upload files!")
        return

    if not any([message.document, message.photo, message.video, message.audio]):
        await message.reply_text("❌ Please send a file (photo/video/document/audio)!")
        return

    raw_token = uuid.uuid4().hex
    file_id = f"file_{raw_token}"
    random_key = uuid.uuid4().hex[:12]
    storage_copy = await context.bot.copy_message(
        chat_id=STORAGE_CHANNEL_ID,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )

    file_name = (
        message.document.file_name
        if message.document and message.document.file_name
        else f"{file_id}.jpg"
        if message.photo
        else f"{file_id}.mp4"
        if message.video
        else f"{file_id}.mp3"
    )

    telegram_file_id = (
        message.document.file_id
        if message.document
        else message.video.file_id
        if message.video
        else message.audio.file_id
        if message.audio
        else message.photo[-1].file_id
        if message.photo
        else None
    )

    media_title = (
        message.video.file_name
        if message.video and message.video.file_name
        else message.document.file_name
        if message.document and message.document.file_name
        else message.audio.title
        if message.audio and message.audio.title
        else message.audio.file_name
        if message.audio and message.audio.file_name
        else message.caption
        if message.caption
        else file_name
    )

    # Ensure user exists in database before adding file record (foreign key constraint)
    save_user(
        user_id=update.effective_user.id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
    )

    store_uploaded_file(
        file_id=file_id,
        file_name=file_name,
        user_id=update.effective_user.id,
        storage_message_id=storage_copy.message_id,
        storage_chat_id=STORAGE_CHANNEL_ID,
        link_token=raw_token,
        telegram_file_id=telegram_file_id,
        media_title=media_title,
        random_key=random_key,
    )

    # Use BOT_TOKEN1's username for share link if available
    bot_username = await _get_share_bot_username()
    if not bot_username:
        # Fallback to current bot's username
        bot_username = (await context.bot.get_me()).username or ""

    link = build_share_link(bot_username, file_id)

    reply_markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔗 Share Link", url=link)],
            [InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_{file_id}")],
        ]
    )

    expires_text = "Never" if NEVER_EXPIRE_LINKS else f"{FILE_EXPIRY_MINUTES} minutes"
    await message.reply_text(
        (
            "✅ File Locked Successfully!\n\n"
            f"📄 File: {escape(file_name)}\n"
            "📤 Stored in: STORAGE_CHANNEL_ID\n"
            f"🔗 Share Link:\n<code>{escape(link)}</code>\n\n"
            f"⏰ Expires: {expires_text}"
        ),
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )
