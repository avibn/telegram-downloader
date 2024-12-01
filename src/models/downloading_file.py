import asyncio
import time
from dataclasses import InitVar, dataclass
from datetime import datetime


@dataclass
class DownloadingFile:
    file_name: str
    file_size: int
    mime_type: str
    start_time: float = time.time()
    cancel_event: asyncio.Event = asyncio.Event()
    _received_bytes: int = 0
    _total_bytes: int = 0
    _start_datetime: InitVar[datetime] = None

    def __post_init__(self, _start_datetime):
        self._start_datetime = _start_datetime or datetime.now()

    def update_progress(self, received_bytes: int, total_bytes: int):
        self._received_bytes = received_bytes
        self._total_bytes = total_bytes

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

    @property
    def received_mb(self) -> str:
        return self.convert_size(self._received_bytes)

    @property
    def total_mb(self) -> str:
        return self.convert_size(self._total_bytes)

    @property
    def progress(self) -> float:
        if self._total_bytes == 0:
            return 0

        return self._received_bytes / self._total_bytes * 100

    @staticmethod
    def convert_duration(time_taken: float) -> str:
        return f"{time_taken:.2f} secs  ({time_taken / 60:.2f} mins)"

    @staticmethod
    def convert_size(size: int) -> str:
        return f"{size / 1024 / 1024:.2f} MB"
