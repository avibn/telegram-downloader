import time

from telethon import types


def get_file_name(document: types.Document) -> str:
    """
    Get the file name from the Telegram document (from a message).

    Args:
        document (types.Document): The telegram document to get the file name from.

    Returns:
        str: The file name of the document.
    """
    file_name_attrs = filter(
        lambda x: isinstance(x, types.DocumentAttributeFilename), document.attributes
    )
    file_name = next(file_name_attrs).file_name
    return file_name if file_name else f"unnamed_{time.time()}"
