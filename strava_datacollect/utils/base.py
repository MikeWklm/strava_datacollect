import functools
from datetime import datetime
from pathlib import Path

import pytz
import schedule


def make_path(pth: str) -> Path:
    return Path.cwd() / pth


def save_datetime_now() -> datetime:
    now = datetime.utcnow()
    now_here = now.astimezone(pytz.timezone('Europe/Berlin'))
    return now_here


def do_only_once(func):
    @functools.wraps(func)
    def wrapper_do_only_once(*args, **kwargs):
        func(*args, **kwargs)
        return schedule.CancelJob
    return wrapper_do_only_once
