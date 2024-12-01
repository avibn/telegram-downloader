import logging
import os
import shutil

from telethon import types
from telethon.events import NewMessage

from ..middlewares.handlers import command_handler, commands
from ..utils import env

logger = logging.getLogger(__name__)


@command_handler(pattern="/help", description="Get help")
async def help(event: NewMessage.Event) -> None:
    """Send a list of available commands to the user."""
    commands_list = "The following commands are available:\n" + "\n".join(
        [f"{key} - {value}" for key, value in commands.items()]
    )
    await event.reply(
        f"{commands_list}\n\nSend me a file and I'll download it to `{env.DOWNLOAD_TO_DIR}`.",
    )


@command_handler(pattern="/start", description="Start the bot")
async def start(event: NewMessage.Event) -> None:
    """Send a start message to the user."""
    sender: types.User = await event.get_sender()

    await event.reply(
        f"Hi [{sender.first_name}](tg://user?id={sender.id})! "
        "I'm a bot that can download files for you. "
        "Send me a file and I'll download it for you.\n\n"
        "Use /help to see available commands.",
    )


@command_handler(pattern="/info", description="Get user and chat info")
async def info(event: NewMessage.Event) -> None:
    """Send user and chat IDs to the user."""
    await event.reply(
        f"**User ID**: {event.sender_id}\n**Chat ID**: {event.chat_id}",
    )


@command_handler(
    pattern="/storage", description="Get available storage information", admin_only=True
)
async def storage(event: NewMessage.Event) -> None:
    """Send available storage information of the specified folder."""
    if os.path.exists(env.DOWNLOAD_TO_DIR):
        total, used, free = shutil.disk_usage(env.DOWNLOAD_TO_DIR)
        await event.reply(
            f"📂 **Folder**:   `{env.DOWNLOAD_TO_DIR}`\n"
            f"🟣 **Total Space**:   `{total // (2**30)} GB`\n"
            f"🟠 **Used Space**:   `{used // (2**30)} GB`\n"
            f"🟢 **Free Space**:    `{free // (2**30)} GB`",
        )
    else:
        await event.reply("The specified folder does not exist.")
