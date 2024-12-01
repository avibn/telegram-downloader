import time
from datetime import datetime, timedelta


def calculate_download_eta(current, total, start_time):
    """
    Calculate the estimated completion time for a download.

    Args:
        current (int): The current number of bytes downloaded.
        total (int): The total number of bytes to be downloaded.
        start_time (float): The start time of the download in seconds.

    Returns:
        str: The estimated completion time in HH:MM format.
    """
    current_time = time.time()
    elapsed_time = current_time - start_time
    download_speed = current / elapsed_time if elapsed_time > 0 else 0

    remaining_bytes = total - current
    estimated_time_remaining = (
        remaining_bytes / download_speed if download_speed > 0 else float("inf")
    )

    estimated_completion_time = datetime.now() + timedelta(
        seconds=estimated_time_remaining
    )
    return estimated_completion_time.strftime("%H:%M")
