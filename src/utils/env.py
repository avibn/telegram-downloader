import logging

from dotenv import load_dotenv
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    BOT_TOKEN: str
    DOWNLOAD_TO_DIR: str
    USER_ID: int
    CHAT_ID: int
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str


logger.info("Loading environment variables")

try:
    logger.info("Loading environment variables")
    env = Settings(_env_file=".env", _env_file_encoding="utf-8")
except ValidationError as e:
    logger.error("Environment variables validation error: %s", e)
    exit(1)
