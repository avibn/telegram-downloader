def trancute_message(message: str, limit: int = 4096, reverse: bool = False) -> str:
    """
    Truncate a message to a specified character limit, appending "..." if truncated.

    Args:
        message (str): The message to be truncated.
        limit (int, optional): The maximum length of the message.
            Defaults to telegram's character limit (4096).
        reverse (bool, optional): Whether to truncate the message from the end.

    Returns:
        str: The truncated message if it exceeds the limit, otherwise the original message.
    """
    if len(message) > limit:
        return (
            message[: limit - 3] + "..."
            if not reverse
            else "..." + message[-(limit - 3) :]
        )

    return message
