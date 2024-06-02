import logging
import os
import shutil
import time

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Environment variables
load_dotenv()

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Help!")


async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Download command received")

    # Check if file exists in DOWNLOAD_TO_DIR already
    if os.path.exists(DOWNLOAD_TO_DIR + update.message.document.file_name):
        await update.message.reply_text("File already exists in downloads folder.")
        return

    # File details
    file_id = update.message.document.file_id
    file_name = update.message.document.file_name
    file_size = update.message.document.file_size / 1024 / 1024  # in MB

    # Send start message
    await update.message.reply_text(
        f"Downloading file...\nFile name: {file_name}\nFile size: {file_size} MB"
    )
    start_time = time.time()

    try:
        newFile = await context.bot.get_file(file_id, read_timeout=1000)
    except Exception as e:
        await update.message.reply_text(f"File size: {file_size}\nError: {e}")
        return

    # Work out time taken to download file
    end_time = time.time()
    download_time = end_time - start_time
    file_path = newFile.file_path.split("/")[
        -1
    ]  # "./documents/file_1.mkv" to "file_1.mkv"
    downloaded_file_size = newFile.file_size / 1024 / 1024  # in MB

    # Rename the file to the original file name
    current_file_path = f"{BOT_API_DIR}{TOKEN_SUB_DIR}/documents/{file_path}"
    move_to_path = f"{DOWNLOAD_TO_DIR}{file_name}"

    # Make DOWNLOAD_TO_DIR if it doesn't exist
    os.makedirs(DOWNLOAD_TO_DIR, exist_ok=True)
    shutil.move(current_file_path, move_to_path)

    await update.message.reply_text(
        f"""
File downloaded successfully.\n
Time taken:    {download_time:.5f} seconds\n
File path:     {file_path}\n
File name:     {file_name}\n
File size:     {downloaded_file_size:.2f} MB"""
    )


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

    # on file upload - download the file
    application.add_handler(MessageHandler(filters.Document.VIDEO, download))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
