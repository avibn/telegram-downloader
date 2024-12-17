import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .cogs import downloader_commands, error_handler, general_commands
from .utils import env

logger = logging.getLogger(__name__)


async def bad_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Raise an error to trigger the error handler."""
    await context.bot.wrong_method_name()  # type: ignore[attr-defined]


def main() -> None:
    # Create the Application and pass it your bot's token.
    application = (
        Application.builder()
        .token(env.BOT_TOKEN)
        .concurrent_updates(True)
        .local_mode(True)
        .base_url(f"{env.LOCAL_BOT_API_URL}/bot")
        .base_file_url(f"{env.LOCAL_BOT_API_URL}/file/bot")
        .build()
    )

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("bad_command", bad_command))
    application.add_handlers(general_commands)
    application.add_handlers(downloader_commands)

    # error handler
    application.add_error_handler(error_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
