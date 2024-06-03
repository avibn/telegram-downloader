import os
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

USER_ID = os.getenv("USER_ID")
CHAT_ID = os.getenv("CHAT_ID")

if not all([USER_ID, CHAT_ID]):
    raise ValueError("Please set USER_ID and CHAT_ID in .env file")


def auth_required(func):
    """
    Decorator that checks if the user and chat are authorized before executing the decorated function.

    Args:
        func (callable): The function to be decorated.

    Example:
        @auth_required
        async def my_function(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            # Function implementation
    """

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if (
            str(update.effective_user.id) != USER_ID
            or str(update.effective_chat.id) != CHAT_ID
        ):
            await update.effective_message.reply_text(
                "Unauthorized user or chat.\n"
                "Please verify the values of `USER_ID` and `CHAT_ID` in environment variables.",
                parse_mode="markdown",
            )
            return
        return await func(update, context)

    return wrapper
