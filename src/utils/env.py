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
    LOCAL_BOT_API_URL: str
    BOT_API_DIR: str
    DOWNLOAD_TO_DIR: str
    USER_ID: int
    CHAT_ID: int


logger.info("Loading environment variables")

try:
    logger.info("Validating environment variables")
    env = Settings()
except ValidationError as e:
    logger.error("Environment variables validation error: %s", e)
    exit(1)
