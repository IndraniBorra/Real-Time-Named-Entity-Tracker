"""
Utility functions for the consumer package
"""

import logging
from datetime import datetime


def setup_logging(name: str, level=logging.INFO):
    """
    Configure logging for consumer components

    Args:
        name: Logger name
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(name)


def format_timestamp(dt: datetime = None) -> str:
    """
    Format datetime as ISO string

    Args:
        dt: Datetime object (defaults to now)

    Returns:
        ISO formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def safe_get(dictionary: dict, *keys, default=''):
    """
    Safely get nested dictionary values

    Args:
        dictionary: Dictionary to search
        *keys: Keys to traverse
        default: Default value if key not found

    Returns:
        Value at key path or default
    """
    result = dictionary
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key, default)
        else:
            return default
    return result
