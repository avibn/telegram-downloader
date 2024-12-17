import asyncio
import logging
import math
import os
import platform
import shutil
import traceback

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes, filters

from ..middlewares.auth import auth_required
from ..middlewares.handlers import (
    callback_query_handler,
    command_handler,
    message_handler,
)
from ..models import DownloadFile, downloading_files
from ..utils import check_file_exists, env, get_file

logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = env.BOT_TOKEN
BOT_API_DIR = env.BOT_API_DIR
DOWNLOAD_TO_DIR = env.DOWNLOAD_TO_DIR

# Replacing colons with a different character for Windows
TOKEN_SUB_DIR = BOT_TOKEN.replace(":", "") if os.name == "nt" else BOT_TOKEN


@command_handler("status")
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send downloading files status to the user."""
    if not downloading_files:
        await update.message.reply_text("No files are being downloaded at the moment.")
        return

    status_message = "*Downloading files status:*\nPage 1\n"

    for i, file in enumerate(downloading_files.values(), start=1):
        file_status = (
            f"> 📄 *File name:*   `{file.file_name}`\n"
            f"> 💾 *File size:*   `{file.file_size_mb}`\n"
            f"> ⏰ *Start time:*   `{file.start_datetime}`\n"
            f"> ⏱ *Duration:*   `{file.current_download_duration}`\n"
            f"> 🔻 *Retries:*   `{file.download_retries}`\n"
            f"> 🔄 *Status:*   `{file.status}`\n\n"
        )
        status_message += file_status

        if i % 2 == 0 or i == len(downloading_files):
            # Add page number
            if i > 2:
                status_message = f"Page {math.ceil(i / 2)}\n" + status_message

            await context.bot.send_message(
                chat_id=update.message.chat_id,
                text=status_message,
                parse_mode="MarkdownV2",
            )
            status_message = ""
            await asyncio.sleep(0.3)


@message_handler(filters.Document.VIDEO)
@auth_required
async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Download the file sent by the user."""
    logger.info("Download command received")

    try:
        check_file_exists(
            update.message.document.file_id, update.message.document.file_name
        )
    except Exception as e:
        logger.error(f"Error checking file exists: {e}")
        await update.message.reply_text(
            f"⛔ File already exists\!\nError:```\n{e}```",
            parse_mode="MarkdownV2",
        )
        return

    # File details
    file_name = update.message.document.file_name
    file_size = DownloadFile.convert_size(update.message.document.file_size)

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
    file_id = message.document.file_id
    file_name = message.document.file_name
    file_size = message.document.file_size

    # Remove buttons from the message
    await update.effective_message.edit_reply_markup(reply_markup=None)

    if query.data == "yes":
        logger.info("Downloading file...")

        # Check if file already exists or is being downloaded
        try:
            check_file_exists(file_id, file_name)
        except Exception as e:
            logger.error(f"Error checking file exists: {e}")
            await message.reply_text(f"⛔ Error checking if file exists\n```\n{e}```")
            return

        # Add file to downloading_files
        download_file = DownloadFile(
            file_id,
            file_name,
            file_size,
        )
        downloading_files[file_id] = download_file

        # Send downloading message
        await message.reply_text("⬇️ Downloading file...")

        try:
            new_file = await get_file(context.bot, download_file)
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            traceback.print_exc()

            # Remove from current downloading files
            downloading_files.pop(file_id)

            await message.reply_text(
                (
                    f"⛔ Error downloading file\n"
                    f"> 📄 *File name:*   `{download_file.file_name}`\n"
                    f"> 💾 *File size:*   `{download_file.file_size_mb}`\n"
                    f"```\n{e}```"
                ),
                parse_mode="MarkdownV2",
            )
            return

        # Remove file from downloading_files
        downloading_files.pop(file_id)
        download_file.download_complete()

        # Rename the file to the original file name
        file_path = new_file.file_path.split("/")[-1]
        current_file_path = f"{BOT_API_DIR}{TOKEN_SUB_DIR}/documents/{file_path}"
        move_to_path = f"{DOWNLOAD_TO_DIR}{file_name}"

        # Move the file to the download directory
        try:
            os.makedirs(DOWNLOAD_TO_DIR, exist_ok=True)

            # todo -- if same disk, just rename
            await asyncio.to_thread(shutil.move, current_file_path, move_to_path)
            download_file.move_complete()
        except Exception as e:
            logger.error(f"Error moving file: {e}")
            await message.reply_text(
                (
                    f"⛔ Error moving file\n"
                    f"> 📂 *File path:*   `{file_path}`\n"
                    f"> 📂 *Move to path:*   `{move_to_path}`\n"
                    f"```\n{e}```"
                ),
                parse_mode="MarkdownV2",
            )
            return

        # If linux, give file correct permissions
        if platform.system() == "Linux":
            os.chmod(move_to_path, 0o664)

        response_message = (
            f"✅ File downloaded successfully\\.\n\n"
            f"> 📄 *File name:*   `{download_file.file_name}`\n"
            f"> 📂 *File path:*   `{file_path}`\n"
            f"> 💾 *File size:*   `{download_file.file_size_mb}`\n"
            f"> 🔻 *Retries:*   `{download_file.download_retries}`\n"
            f"> ⏱ *Download Duration:*   `{download_file.download_duration}`\n"
            f"> ⏱ *Moving Duration:*   `{download_file.move_duration}`\n"
            f"> ⏱ *Total Duration:*   `{download_file.total_duration}`"
        )

        await message.reply_text(response_message, parse_mode="MarkdownV2")
    else:
        logger.info("Download cancelled")
        await message.reply_text("Download cancelled.")
