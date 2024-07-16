import html
import logging
import os
import traceback

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

USER_ID = os.getenv("USER_ID")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Join the traceback error
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    # Build the error message
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "An exception was raised while handling an update\n"
        # f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        # "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Send the error message to the developer
    await context.bot.send_message(chat_id=USER_ID, text=message, parse_mode="HTML")

    # Send error message in chat
    await update.message.reply_text(
        "An error occurred while processing the request. Please check the logs."
    )
