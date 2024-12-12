import time
from dataclasses import InitVar, dataclass
from datetime import datetime


@dataclass
class DownloadFile:
    file_id: str
    file_name: str
    file_size: int
    start_time: float
    download_retries: int = 0
    _start_datetime: InitVar[datetime] = None

    def __post_init__(self, _start_datetime):
        self._start_datetime = _start_datetime or datetime.now()

    @property
    def start_datetime(self) -> str:
        return self._start_datetime.strftime("%H:%M:%S  %d/%m/%Y")

    @property
    def file_size_mb(self) -> str:
        return f"{self.file_size / 1024 / 1024:.2f} MB"

    @property
    def download_time(self) -> str:
        time_taken = time.time() - self.start_time
        return self.convert_duration(time_taken)

    @staticmethod
    def convert_duration(time_taken: float) -> str:
        return f"{time_taken:.2f} secs  ({time_taken / 60:.2f} mins)"

    @staticmethod
    def convert_size(size: int) -> str:
        return f"{size / 1024 / 1024:.2f} MB"


# Current downloading files
downloading_files: dict[str, DownloadFile] = {}
