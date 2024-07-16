import logging
import os
import platform
import shutil
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, filters

from ..middlewares.auth import auth_required
from ..middlewares.handlers import (
    callback_query_handler,
    command_handler,
    message_handler,
)
from ..models import DownloadingFile

logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_API_DIR = os.getenv("BOT_API_DIR")
DOWNLOAD_TO_DIR = os.getenv("DOWNLOAD_TO_DIR")

# Replacing colons with a different character for Windows
TOKEN_SUB_DIR = BOT_TOKEN.replace(":", "") if os.name == "nt" else BOT_TOKEN

# Current downloading files
downloading_files: dict[str, DownloadingFile] = {}


def check_file_exists(file_id: str, file_name: str) -> tuple[bool, str]:
    """
    Check if a file exists in the download directory or is currently being downloaded.

    Args:
        file_id (str): The ID of the file to check.
        file_name (str): The name of the file to check.

    Returns:
        tuple[bool, str]: A tuple containing a boolean value and a message.
    """
    if os.path.exists(DOWNLOAD_TO_DIR + file_name):
        return True, "File already exists in downloads folder."

    if file_id in downloading_files:
        return True, "File is already being downloaded."

    # Check file_name in downloading_files
    if any(file.file_name == file_name for file in downloading_files.values()):
        return True, "File is already being downloaded."

    return False


@command_handler("status")
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


@message_handler(filters.Document.VIDEO)
@auth_required
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download the file sent by the user."""
    logger.info("Download command received")

    # Check if file already exists or is being downloaded
    if check := check_file_exists(
        update.message.document.file_id, update.message.document.file_name
    ):
        await update.message.reply_text(check[1])
        return

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
    await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=response_message,
        reply_to_message_id=update.message.message_id,
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


@callback_query_handler()
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

        # Check if file already exists or is being downloaded
        if check := check_file_exists(message.document.file_id, file_name):
            await message.reply_text(check[1])
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
