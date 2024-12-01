import logging
import os
import platform
import time

from telethon import Button, types
from telethon.events import CallbackQuery, NewMessage

from ..middlewares.handlers import (
    callback_handler,
    command_handler,
)
from ..models import DownloadingFile
from ..utils import (
    calculate_download_eta,
    check_file_exists,
    create_blockquote,
    get_file_name,
)
from ..utils.env import env

logger = logging.getLogger(__name__)

# Current downloading files
downloading_files: dict[str, DownloadingFile] = {}


@command_handler(
    pattern="/status", description="Get downloading files status", admin_only=True
)
async def status(event: NewMessage.Event) -> None:
    """Send downloading files status to the user."""
    if not downloading_files:
        await event.reply("No files are being downloaded at the moment.")
        return

    status_message = "<strong>Downloading files status:</strong>\n\n"
    for file in downloading_files.values():
        status_message += create_blockquote(
            {
                "📄File name": file.file_name,
                "💾File size": file.file_size_mb,
                "⏰Start time": file.start_datetime,
                "⏱Duration": file.download_time,
                "⏳Data received": f"{file.received_mb}/{file.total_mb}",
                "⏳Progress": f"{file.progress:.2f}%",
            }
        )

    await event.reply(status_message, parse_mode="html")


@command_handler()
async def download(event: NewMessage.Event) -> None:
    """Download the file sent by the user."""
    logger.info("Download command received")

    message: types.Message = event.message
    if not message.media:
        return

    document = message.media.document
    file_name = get_file_name(document)

    # Check if file already exists or is being downloaded
    check = check_file_exists(document.id, file_name, downloading_files)
    if check.exists:
        await event.reply(check.message)
        return

    file_size = DownloadingFile.convert_size(document.size)

    response_message = (
        "Are you sure you want to download the file?\n\n"
        + create_blockquote(
            {
                "📄File name": file_name,
                "💾File size": file_size,
            }
        )
    )

    # Confirmation message
    await event.reply(
        message=response_message,
        buttons=[
            [
                Button.inline("Yes", b"yes"),
                Button.inline("No", b"no"),
            ],
        ],
        parse_mode="html",
    )


@callback_handler(admin_only=True)
async def callback(event: CallbackQuery.Event):
    """Handle the confirmation button click for downloading the file."""
    logger.info("Button command received")

    # Get replied message
    confirm_message = await event.get_message()
    video_message = await confirm_message.get_reply_message()

    # Remove buttons
    await confirm_message.edit(buttons=None, parse_mode="html")

    if event.data == b"yes":
        logger.info("Downloading file...")
        document = video_message.media.document
        file_name = get_file_name(document)

        # Check if file already exists or is being downloaded
        check = check_file_exists(document.id, file_name, downloading_files)
        if check.exists:
            return await event.reply(check.message)

        downloading_message = await event.reply("⬇️ Downloading file...")

        # Store file metadata
        downloading_file = DownloadingFile(
            file_name=file_name,
            file_size=document.size,
            mime_type=document.mime_type,
        )
        downloading_files[document.id] = downloading_file
        file_path = os.path.join(env.DOWNLOAD_TO_DIR, file_name)
        last_progress_edit = 0

        async def progress_callback(current, total):
            """
            Callback function to update the download progress.
            Args:
                current (int): The current amount of data downloaded.
                total (int): The total amount of data to be downloaded.
            """
            nonlocal last_progress_edit
            nonlocal downloading_file

            current_time = time.time()
            downloading_file.update_progress(current, total)

            estimated_completion_time_str = calculate_download_eta(
                current, total, downloading_file.start_time
            )

            if (current_time - last_progress_edit >= 10) or (current == total):
                last_progress_edit = current_time
                await downloading_message.edit(
                    "⏳ Downloading\n\n"
                    f"`ETA: {estimated_completion_time_str}`\n"
                    f"`{downloading_file.received_mb}/{downloading_file.total_mb}`\n"
                    f"`{downloading_file.progress:.2f}%`\n"
                )

        # Download the file
        try:
            await video_message.download_media(
                file=file_path, progress_callback=progress_callback
            )

            await downloading_message.edit("✅ File downloaded successfully.")
        except Exception as e:
            error_response = "⛔ Error downloading file.\n\n" + create_blockquote(
                {
                    "📄File name": downloading_file.file_name,
                    "💾File size": downloading_file.file_size_mb,
                    "⚠️Error": str(e),
                }
            )
            return await event.reply(
                error_response,
                parse_mode="html",
            )

        # Remove file from downloading_files
        downloading_files.pop(document.id)

        # If linux, give file correct permissions
        if platform.system() == "Linux":
            os.chmod(file_path, 0o664)

        dowload_duration = DownloadingFile.convert_duration(
            time.time() - downloading_file.start_time
        )

        response_message = "✅ File downloaded successfully.\n\n" + create_blockquote(
            {
                "📄File name": downloading_file.file_name,
                "📂File path": file_path,
                "💾File size": downloading_file.file_size_mb,
                "⏱Download Duration": dowload_duration,
            }
        )
        await event.reply(response_message, parse_mode="html")

    else:
        await event.reply("❌ Download cancelled.")
