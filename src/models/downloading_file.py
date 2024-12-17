from dataclasses import InitVar, dataclass
from datetime import datetime, timedelta


@dataclass
class DownloadFile:
    file_id: str
    file_name: str
    file_size: int
    download_retries: int = 0
    _start_datetime: InitVar[datetime] = None
    _finish_download_datetime: datetime = None
    _finish_move_datetime: datetime = None

    def __post_init__(self, _start_datetime):
        self._start_datetime = _start_datetime or datetime.now()

    def download_complete(self):
        self._finish_download_datetime = datetime.now()

    def move_complete(self):
        self._finish_move_datetime = datetime.now()

    @property
    def current_download_duration(self) -> str:
        duration = datetime.now() - self._start_datetime
        return self.convert_duration(duration)

    @property
    def download_duration(self) -> str:
        duration = self._finish_download_datetime - self._start_datetime
        return self.convert_duration(duration)

    @property
    def move_duration(self) -> str:
        duration = self._finish_move_datetime - self._finish_download_datetime
        return self.convert_duration(duration)

    @property
    def total_duration(self) -> str:
        duration = self._finish_move_datetime - self._start_datetime
        return self.convert_duration(duration)

    @property
    def start_datetime(self) -> str:
        return self._start_datetime.strftime("%H:%M:%S  %d/%m/%Y")

    @property
    def file_size_mb(self) -> str:
        return self.convert_size(self.file_size)

    @property
    def status(self) -> str:
        if self._finish_move_datetime:
            return "Complete"
        if self._finish_download_datetime:
            return "Moving"
        return "Downloading"

    @staticmethod
    def convert_duration(time_taken: timedelta) -> str:
        total_minutes = time_taken.total_seconds() / 60
        return f"{time_taken.total_seconds():.2f} secs  ({total_minutes:.2f} mins)"

    @staticmethod
    def convert_size(size: int) -> str:
        return f"{size / 1024 / 1024:.2f} MB"


# Current downloading files
downloading_files: dict[str, DownloadFile] = {}
