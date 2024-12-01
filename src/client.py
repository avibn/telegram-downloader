from telethon import TelegramClient

from .utils import env

# Telegram API
client = TelegramClient("bot", env.TELEGRAM_API_ID, env.TELEGRAM_API_HASH).start(
    bot_token=env.BOT_TOKEN
)
