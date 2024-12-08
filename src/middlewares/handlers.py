from functools import wraps
from typing import Any, Callable, Optional, Pattern, Union

from telethon.events import CallbackQuery, NewMessage

from ..client import client
from ..utils import env

commands: dict[Union[str, Pattern], str] = {}


def command_handler(
    pattern: Optional[Union[str, Callable[[str], bool], Pattern]] = None,
    admin_only: bool = False,
    description: Optional[str] = None,
):
    def decorator(func: Callable[[NewMessage.Event], Any]):
        @wraps(func)
        async def wrapper(event: NewMessage.Event):
            if admin_only and event.sender_id != env.USER_ID:
                return await event.respond(
                    "You are not authorized to use this command."
                )

            if env.CHAT_ID != event.chat_id:
                return await event.respond(
                    "This command can only be used in the specified chat."
                )

            return await func(event)

        # Add the command to the list of available commands
        if description:
            command_name = pattern if pattern else f"`{func.__name__}`"
            commands[command_name] = description

        # Define the event parameters
        event_params = {}
        if pattern:
            event_params["pattern"] = pattern
        # if admin_only: event_params["from_users"] = USER_ID

        # Register event handler
        client.on(NewMessage(**event_params))(wrapper)
        return wrapper

    return decorator


def callback_handler(
    data: Optional[Union[bytes, str, Callable[[str], bool]]] = None,
    pattern: Optional[Union[str, Callable[[str], bool], Pattern]] = None,
    admin_only: bool = False,
):
    def decorator(func: Callable[[CallbackQuery.Event], Any]):
        @wraps(func)
        async def wrapper(event: CallbackQuery.Event):
            if admin_only and event.sender_id != env.USER_ID:
                return await event.respond(
                    "You are not authorized to use this command."
                )
            return await func(event)

        # Define the event parameters
        event_params = {}
        if pattern:
            event_params["pattern"] = pattern

        # Register event handler
        client.on(CallbackQuery(**event_params))(wrapper)
        return wrapper

    return decorator
