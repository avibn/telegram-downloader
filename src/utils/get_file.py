import asyncio
import logging
import os

from telegram import Bot, File
from telegram.error import NetworkError

from src.utils.env import env

from ..models import DownloadFile, downloading_files

logger = logging.getLogger(__name__)

# Retry constants
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 5

# Environment variables
DOWNLOAD_TO_DIR = env.DOWNLOAD_TO_DIR


async def get_file(bot: Bot, file: DownloadFile) -> File:
    """
    Download a file from Telegram with retry logic.
    Args:
        bot (Bot): The bot instance used to download the file.
        file (DownloadFile): The download file object (containing file_id).
    Returns:
        File: The downloaded file object.
    Raises:
        Exception: If the maximum number of retries is reached/non network error occurs
        or file already exists.
    """
    for i in range(MAX_RETRIES):
        # Log attempt
        logger.info(f"Downloading file, attempt {i + 1}")
        file.download_retries = i

        # Check if file exists in directory already
        check_file_exists(file.file_id, file.file_name, check_downloading_files=False)

        try:
            new_file = await bot.get_file(file.file_id, read_timeout=1800)
            logger.info("File downloaded successfully")
            break
        except NetworkError as e:
            logger.error(f"Server disconnect error: {e}")
            await asyncio.sleep(INITIAL_RETRY_DELAY * i)

    else:
        raise Exception("Max retries reached")

    return new_file


def check_file_exists(
    file_id: str, file_name: str, check_downloading_files: bool = True
) -> bool:
    """
    Check if a file exists in the download directory or is currently being downloaded.

    Args:
        file_id (str): The ID of the file to check.
        file_name (str): The name of the file to check.
        check_downloading_files (bool): Whether to check the downloading_files dictionary.

    Returns:
        bool: True if the file exists

    Raises:
        Exception: If the file already exists in the download directory or is being downloaded.
    """
    if os.path.exists(DOWNLOAD_TO_DIR + file_name):
        raise Exception("File already exists in downloads folder.")

    if check_downloading_files:
        if file_id in downloading_files:
            raise Exception("File is already being downloaded.")

        # Check file_name in downloading_files
        if any(file.file_name == file_name for file in downloading_files.values()):
            raise Exception("File is already being downloaded.")

    return True
