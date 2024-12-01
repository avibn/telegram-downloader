def create_blockquote(input_dict: dict) -> str:
    """
    Generates an HTML blockquote element with the contents of the input dictionary.
    Args:
        input_dict (dict): A input dictionary containing key-value pairs to be formatted.
    Returns:
        str: A string containing the HTML blockquote element with the formatted contents.
    """
    content = ""
    for key, value in input_dict.items():
        content += f"<strong>{key}:</strong>  <code>{value}</code>\n"

    return "<blockquote>" + content + "</blockquote>"
