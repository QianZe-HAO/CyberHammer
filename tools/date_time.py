import datetime


def get_current_datetime(output_format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Get the current date and time as a formatted string.
    Args:
        output_format (str): The datetime format string. Default is "%Y-%m-%d %H:%M:%S".
    Returns:
        str: Formatted current datetime string.
    """
    return datetime.datetime.now().strftime(output_format)


def get_current_timestamp() -> float:
    """
    Get the current Unix timestamp in seconds.
    Returns:
        float: Current timestamp.
    """
    return datetime.datetime.now().timestamp()


def convert_timestamp_to_datetime(
    timestamp: float, output_format: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    Convert a Unix timestamp to a formatted datetime string.
    Args:
        timestamp (float): Unix timestamp in seconds.
        output_format (str): The format for the output string.
    Returns:
        str: Formatted datetime string.
    """
    return datetime.datetime.fromtimestamp(timestamp).strftime(output_format)
