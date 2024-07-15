# Environment variables
from dotenv import load_dotenv

load_dotenv(override=True)

import html
import logging
import os
import platform
import shutil
import time
import traceback

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .middlewares.auth import auth_required
from .models import DownloadingFile

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOCAL_BOT_API_URL = os.getenv("LOCAL_BOT_API_URL")
BOT_API_DIR = os.getenv("BOT_API_DIR")
DOWNLOAD_TO_DIR = os.getenv("DOWNLOAD_TO_DIR")
USER_ID = os.getenv("USER_ID")

if not all([BOT_TOKEN, LOCAL_BOT_API_URL, BOT_API_DIR, DOWNLOAD_TO_DIR]):
    raise ValueError("Please set all environment variables in .env file")

# Replacing colons with a different character for Windows
TOKEN_SUB_DIR = BOT_TOKEN.replace(":", "") if os.name == "nt" else BOT_TOKEN

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# List of available commands
commands = {
    "/start": "Start the bot",
    "/help": "Get help",
    "/info": "Get user and chat info",
    "/status": "Get downloading files status",
}


# Current downloading files
downloading_files: dict[str, DownloadingFile] = {}


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a list of available commands to the user."""
    commands_list = "The following commands are available:\n" + "\n".join(
        [f"{key} - {value}" for key, value in commands.items()]
    )
    await update.message.reply_text(
        f"{commands_list}\n\nSend me a file and I'll download it to `{DOWNLOAD_TO_DIR}`.",
        parse_mode="markdown",
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a start message to the user."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}! I'm a bot that can download files for you. "
        "Send me a file and I'll download it for you.\n\n"
        "Use /help to see available commands."
    )


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send user and chat IDs to the user."""
    user = update.effective_user
    await update.message.reply_text(
        f"*User ID*: {user.id}\n*Chat ID*: {update.effective_chat.id}",
        parse_mode="markdown",
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send downloading files status to the user."""
    if not downloading_files:
        await update.message.reply_text("No files are being downloaded at the moment.")
        return

    status_message = "*Downloading files status:*\n\n"
    for file in downloading_files.values():
        status_message += (
            f"> 📄 *File name:*   `{file.file_name}`\n"
            f"> 💾 *File size:*   `{file.file_size_mb}`\n"
            f"> ⏰ *Start time:*   `{file.start_datetime}`\n"
            f"> ⏱ *Duration:*   `{file.download_time}`\n\n"
        )

    await update.message.reply_text(status_message, parse_mode="MarkdownV2")


@auth_required
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download the file sent by the user."""
    logger.info("Download command received")

    # Check if file exists in DOWNLOAD_TO_DIR already
    if os.path.exists(DOWNLOAD_TO_DIR + update.message.document.file_name):
        await update.message.reply_text("File already exists in downloads folder.")
        return

    # Check if file is already downloading
    if update.message.document.file_id in downloading_files:
        await update.message.reply_text("File is already being downloaded.")

    # File details
    file_id = update.message.document.file_id
    file_name = update.message.document.file_name
    file_size = DownloadingFile.convert_size(update.message.document.file_size)

    response_message = (
        f"Are you sure you want to download the file?\n\n"
        f"> 📄 *File name:*   `{file_name}`\n"
        f"> 💾 *File size:*   `{file_size}`\n"
    )

    # Confirmation message
    await update.message.reply_text(
        response_message,
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Yes", callback_data="yes"),
                    InlineKeyboardButton("No", callback_data="no"),
                ]
            ]
        ),
    )


@auth_required
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the confirmation button click for downloading the file."""
    logger.info("Button command received")
    query = update.callback_query

    await query.answer()

    # Replied to message
    message = update.effective_message.reply_to_message
    file_name = message.document.file_name

    if query.data == "yes":
        logger.info("Downloading file...")

        # Check if file exists in DOWNLOAD_TO_DIR already
        if os.path.exists(DOWNLOAD_TO_DIR + file_name):
            await message.reply_text("File already exists in downloads folder.")
            return

        # Check if file is already downloading
        if message.document.file_id in downloading_files:
            await message.reply_text("File is already being downloaded.")
            return

        start_time = time.time()

        # Add file to downloading_files
        downloading_file = DownloadingFile(
            file_name=file_name,
            file_size=message.document.file_size,
            start_time=start_time,
        )
        downloading_files[message.document.file_id] = downloading_file

        # Send downloading message
        await message.reply_text("⬇️ Downloading file...")

        try:
            newFile = await context.bot.get_file(
                message.document.file_id, read_timeout=1000
            )
        except Exception as e:
            await message.reply_text(
                (
                    f"⛔ Error downloading file.\n\n"
                    f"> 📄 *File name:*   `{downloading_file.file_name}`\n"
                    f"> 💾 *File size:*   `{downloading_file.file_size_mb}`\n"
                    f"Error: ```{e}```"
                ),
                parse_mode="MarkdownV2",
            )
            return

        # Remove file from downloading_files
        downloading_files.pop(message.document.file_id)

        # Work out time taken to download file
        download_complete_time = time.time()
        dowload_duration = DownloadingFile.convert_duration(
            download_complete_time - start_time
        )
        file_path = newFile.file_path.split("/")[-1]

        # Rename the file to the original file name
        current_file_path = f"{BOT_API_DIR}{TOKEN_SUB_DIR}/documents/{file_path}"
        move_to_path = f"{DOWNLOAD_TO_DIR}{file_name}"

        # Make DOWNLOAD_TO_DIR if it doesn't exist
        os.makedirs(DOWNLOAD_TO_DIR, exist_ok=True)
        shutil.move(current_file_path, move_to_path)

        # If linux, give file correct permissions
        if platform.system() == "Linux":
            os.chmod(move_to_path, 0o664)

        # Calculate durations
        complete_time = time.time()
        moving_duration = DownloadingFile.convert_duration(
            complete_time - download_complete_time
        )
        total_duration = DownloadingFile.convert_duration(complete_time - start_time)

        response_message = (
            f"✅ File downloaded successfully\\.\n\n"
            f"> 📄 *File name:*   `{downloading_file.file_name}`\n"
            f"> 📂 *File path:*   `{file_path}`\n"
            f"> 💾 *File size:*   `{downloading_file.file_size_mb}`\n"
            f"> ⏱ *Download Duration:*   `{dowload_duration}`\n"
            f"> ⏱ *Moving Duration:*   `{moving_duration}`\n"
            f"> ⏱ *Total Duration:*   `{total_duration}`\n"
        )

        await message.reply_text(response_message, parse_mode="MarkdownV2")
    else:
        logger.info("Download cancelled")
        await message.reply_text("Download cancelled.")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Join the traceback error
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    # Build the error message
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        # f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        # "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Send the error message to the developer
    await context.bot.send_message(chat_id=USER_ID, text=message, parse_mode="HTML")

    # Send error message in chat
    await update.message.reply_text(
        "An error occurred while processing the request. Please check the logs."
    )


def main() -> None:
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .concurrent_updates(True)
        .local_mode(True)
        .base_url(f"{LOCAL_BOT_API_URL}/bot")
        .base_file_url(f"{LOCAL_BOT_API_URL}/file/bot")
        .build()
    )

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("status", status))

    # on file upload - download the file
    application.add_handler(MessageHandler(filters.Document.VIDEO, download))
    application.add_handler(CallbackQueryHandler(button))

    # error handler
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
