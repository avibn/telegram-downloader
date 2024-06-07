# Environment variables
from dotenv import load_dotenv

load_dotenv()

import logging
import os
import platform
import shutil
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .auth import auth_required

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOCAL_BOT_API_URL = os.getenv("LOCAL_BOT_API_URL")
BOT_API_DIR = os.getenv("BOT_API_DIR")
DOWNLOAD_TO_DIR = os.getenv("DOWNLOAD_TO_DIR")

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
}


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


@auth_required
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download the file sent by the user."""
    logger.info("Download command received")

    # Check if file exists in DOWNLOAD_TO_DIR already
    if os.path.exists(DOWNLOAD_TO_DIR + update.message.document.file_name):
        await update.message.reply_text("File already exists in downloads folder.")
        return

    # File details
    file_id = update.message.document.file_id
    file_name = update.message.document.file_name
    file_size = update.message.document.file_size / 1024 / 1024  # in MB

    # Confirmation message
    ok = await update.message.reply_text(
        f"Download file?\nFile name: {file_name}\nFile size: {file_size:.2f} MB",
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
    file_size = message.document.file_size / 1024 / 1024  # in MB

    if query.data == "yes":
        logger.info("Downloading file...")

        # Check if file exists in DOWNLOAD_TO_DIR already
        if os.path.exists(DOWNLOAD_TO_DIR + file_name):
            await message.reply_text("File already exists in downloads folder.")
            return

        await message.reply_text(
            f"Downloading file...\nFile name: {file_name}\nFile size: {file_size:.2f} MB"
        )
        start_time = time.time()

        try:
            newFile = await context.bot.get_file(
                message.document.file_id, read_timeout=1000
            )
        except Exception as e:
            await message.reply_text(f"File size: {file_size}\nError: {e}")
            return

        # Work out time taken to download file
        end_time = time.time()
        download_time = end_time - start_time
        download_time_mins = download_time / 60
        file_path = newFile.file_path.split("/")[-1]
        downloaded_file_size = newFile.file_size / 1024 / 1024

        # Rename the file to the original file name
        current_file_path = f"{BOT_API_DIR}{TOKEN_SUB_DIR}/documents/{file_path}"
        move_to_path = f"{DOWNLOAD_TO_DIR}{file_name}"

        # Make DOWNLOAD_TO_DIR if it doesn't exist
        os.makedirs(DOWNLOAD_TO_DIR, exist_ok=True)
        shutil.move(current_file_path, move_to_path)

        # If linux, give file correct permissions
        if platform.system() == "Linux":
            os.chmod(move_to_path, 0o664)

        response_message = (
            f"File downloaded successfully.\n"
            f"Time taken:    {download_time:.5f} secs ({download_time_mins:.2f} mins)\n"
            f"File path:     {file_path}\n"
            f"File name:     {file_name}\n"
            f"File size:     {downloaded_file_size:.2f} MB"
        )

        await message.reply_text(response_message)
    else:
        logger.info("Download cancelled")
        await message.reply_text("Download cancelled.")


def main() -> None:
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .local_mode(True)
        .base_url(f"{LOCAL_BOT_API_URL}/bot")
        .base_file_url(f"{LOCAL_BOT_API_URL}/file/bot")
        .build()
    )

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info))

    # on file upload - download the file
    application.add_handler(MessageHandler(filters.Document.VIDEO, download))
    application.add_handler(CallbackQueryHandler(button))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
