import logging

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Import all the cogs
import src.cogs

from .client import client

# List of all handlers
logger.info(
    "Handlers registered - %s",
    [
        (id(callback), event.__class__.__name__)
        for callback, event in client.list_event_handlers()
    ],
)


def main():
    client.start()
    client.run_until_disconnected()
