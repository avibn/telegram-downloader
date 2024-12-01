import os
from dataclasses import dataclass

from .env import env


@dataclass
class FileCheckResult:
    exists: bool
    message: str


def check_file_exists(
    file_id: str, file_name: str, downloading_files: dict
) -> FileCheckResult:
    """
    Check if a file exists in the download directory or is currently being downloaded.

    Args:
        file_id (str): The ID of the file to check.
        file_name (str): The name of the file to check.
        downloading_files (dict): The dictionary containing the downloading files.

    Returns:
        FileCheckResult: A tuple containing the result of the check and a message.
    """
    if os.path.exists(env.DOWNLOAD_TO_DIR + file_name):
        return FileCheckResult(True, "File already exists in downloads folder.")

    if file_id in downloading_files:
        return FileCheckResult(True, "File is already being downloaded.")

    # Check file_name in downloading_files
    if any(file.file_name == file_name for file in downloading_files.values()):
        return FileCheckResult(True, "File is already being downloaded.")

    return FileCheckResult(False, "File is not being downloaded.")
