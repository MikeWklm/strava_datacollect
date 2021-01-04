import functools
from datetime import datetime
from pathlib import Path

import pytz
import schedule


def make_path(pth: str) -> Path:
    """helper function to create a path 
    from a string where the base is cwd

    Args:
        pth (str): path to create

    Returns:
        Path: path object
    """
    return Path.cwd() / pth


def save_datetime_now() -> datetime:
    """helper function to create a timezone save datetime

    Returns:
        datetime: timezone save datetime
    """
    now = datetime.utcnow()
    now_here = now.astimezone(pytz.timezone('Europe/Berlin'))
    return now_here


def do_only_once(func):
    """wrapper (decorater) to execute the given function
    only when when using the schedule module by returning
    a CancelJob instead of the normal output

    Args:
        func ([type]): function to execute only once (
            should return None because the return value can
            not be used
        )

    Returns:
        [type]: the function that returns schedule.CancelJob
    """
    @functools.wraps(func)
    def wrapper_do_only_once(*args, **kwargs):
        func(*args, **kwargs)
        return schedule.CancelJob
    return wrapper_do_only_once
