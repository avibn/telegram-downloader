import html
import logging
import traceback

from telegram import Update
from telegram.ext import ContextTypes

from ..utils import env, trancute_message

logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # Join the traceback error
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    # Build the error messages
    # update_str = update.to_dict() if isinstance(update, Update) else str(update)
    # update_html = f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n\n"

    message_intro = "⚠️ An exception was raised while handling an update\n"
    message_chat_data = trancute_message(
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
    )
    message_user_data = trancute_message(
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
    )
    message_error = trancute_message(
        message=f"<pre>{html.escape(tb_string)}</pre>",
        reverse=True,
    )

    error_messages = [
        message_intro,
        message_chat_data,
        message_user_data,
        message_error,
    ]

    for message in error_messages:
        await context.bot.send_message(
            chat_id=env.USER_ID, text=message, parse_mode="HTML"
        )

    # Send error message in chat
    await update.message.reply_text(
        "An error occurred while processing the request. Please check the logs."
    )
