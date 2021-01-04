import sqlite3
from datetime import datetime
import enum

import pandas as pd
from hydra.utils import call
from omegaconf import DictConfig


class TokenStatus(enum.Enum):
    ACTIVE = 1
    EXPIRED = 2
    NO_TOKEN = 2


def table_exists(con, table: str) -> bool:
    query = f"""
    SELECT name 
    FROM sqlite_master 
    WHERE type='table' 
    AND name='{table}';
    """
    return not pd.read_sql(query, con).empty


def last_update(cfg: DictConfig, table: str, column: str = 'last_update') -> datetime:
    with sqlite3.connect(call(cfg.DB)) as con:
        last_update = con.execute(
            f"""
            SELECT MAX({column})
            FROM {table}
            """,
        ).fetchone()[0]
        # convert string to datetime
    return datetime.fromisoformat(last_update)
