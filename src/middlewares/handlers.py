from typing import Any, Callable, Coroutine, Dict

from telegram import Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ExtBot,
    MessageHandler,
    filters,
)
from telegram.ext.filters import BaseFilter

ApplicationContext = CallbackContext[
    ExtBot[None], Dict[Any, Any], Dict[Any, Any], Dict[Any, Any]
]


# https://github.com/Lur1an/python-telegram-bot-template/blob/master/src/bot/common/context.py
def command_handler(command: str | list[str], *, filters: BaseFilter = filters.ALL):
    def inner_decorator(
        f: Callable[[Update, ApplicationContext], Coroutine[Any, Any, Any]]
    ) -> CommandHandler:
        return CommandHandler(
            filters=filters,
            command=command,
            callback=f,
        )

    return inner_decorator


def message_handler(filters: BaseFilter):
    def inner_decorator(
        f: Callable[[Update, ApplicationContext], Coroutine[Any, Any, Any]]
    ) -> MessageHandler:
        return MessageHandler(filters=filters, callback=f)

    return inner_decorator


def callback_query_handler():
    def inner_decorator(
        f: Callable[[Update, ApplicationContext], Coroutine[Any, Any, Any]]
    ) -> CallbackQueryHandler:
        return CallbackQueryHandler(callback=f)

    return inner_decorator
