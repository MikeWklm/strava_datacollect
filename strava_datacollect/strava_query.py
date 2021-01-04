import sqlite3
import time
from datetime import datetime
from typing import Any, Dict, Optional, Set

import hydra
import numpy as np
import pandas as pd
import schedule
from tqdm import tqdm
from hydra.utils import call
from omegaconf import DictConfig

from strava_datacollect.strava_auth import (MySession, get_token_status,
                                            refresh_token)
from strava_datacollect.utils.base import save_datetime_now
from strava_datacollect.utils.data import (TokenStatus, last_update,
                                           table_exists)


@hydra.main(config_path='config', config_name='config')
def initialize_database(cfg: DictConfig):
    """initializes the database by checking for
    the defined years which activities are available.
    Then firstly the metadata and second the rawdata
    is queried from strava api.

    It is checked via whether or not the data (mata or raw)
    is already available

    Args:
        cfg (DictConfig): configuration

    Returns:
        [type]: cancel command to schedule (basically None)
    """
    ids = set()
    for year in tqdm(cfg.INIT_YEARS, 'Iterating Years'):
        from_ = datetime.fromisoformat(f'{year}-01-01')
        to_ = datetime.fromisoformat(f'{year+1}-01-01')
        ids = ids.union(get_activtiy_ids(cfg, from_, to_))
    avail_meta_ids = get_avail_ids(cfg, 'ACTIVITIES_META')
    avail_raw_ids = get_avail_ids(cfg, 'ACTIVITIES_RAW')
    meta_to_get = ids.difference(avail_meta_ids)
    raw_to_get = ids.difference(avail_raw_ids)
    for id in tqdm(meta_to_get, 'Meta Info'):
        get_activity_metadata(cfg, id)
        if get_token_status(cfg) == TokenStatus.EXPIRED:
            refresh_token(cfg)
    for id in tqdm(raw_to_get, 'Raw Data'):
        get_activity_rawdata(cfg, id)
        if get_token_status(cfg) == TokenStatus.EXPIRED:
            refresh_token(cfg)
    # run this only once
    return schedule.CancelJob


@hydra.main(config_path='config', config_name='config')
def update_meta(cfg: DictConfig) -> None:
    """updates the metadata by looking at the last 
    activtiy and checking if since then new data is available

    Args:
        cfg (DictConfig): configuration
    """
    from_ = last_update(cfg, 'ACTIVITIES_META', 'start_date_local')
    new_ids = get_activtiy_ids(cfg, from_)
    avail_ids = get_avail_ids(cfg, 'ACTIVITIES_META')
    new_ids = new_ids.difference(avail_ids)
    for id in new_ids:
        get_activity_metadata(cfg, id)


@hydra.main(config_path='config', config_name='config')
def update_raw(cfg: DictConfig) -> None:
    """Updates rawdata based on ids in meta which
    are not in raw (so reun udpate_meta always first)

    Args:
        cfg (DictConfig): configuration
    """
    meta_ids = get_avail_ids(cfg, 'ACTIVITIES_META')
    raw_ids = get_avail_ids(cfg, 'ACTIVITIES_RAW')
    new_ids = meta_ids.difference(raw_ids)
    for id in new_ids:
        get_activity_rawdata(cfg, id)


def get_avail_ids(cfg: DictConfig, table: str) -> Set[int]:
    # util function to get all available ids in a table
    query = f"""
    SELECT id
    FROM 
    {table}
    """
    with sqlite3.connect(call(cfg.DB)) as con:
        if table_exists(con, table):
            ids = pd.read_sql(query, con)
            ids = set(ids.iloc[:, 0])
            return ids
        return set()


def get_activtiy_ids(cfg: DictConfig,
                     from_: datetime, to_: Optional[datetime] = save_datetime_now()) -> Set[int]:
    """get activty ids from strava in a given timeperiod

    Args:
        cfg (DictConfig): config
        from_ (datetime): start time
        to_ (Optional[datetime], optional): end time. Defaults to save_datetime_now().

    Returns:
        Set[int]: ids in this timeperiod
    """
    # convert times to epochtime
    from_ = int(from_.timestamp())
    to_ = int(to_.timestamp())
    # get activties in timeframe
    with MySession(cfg) as session:
        res = session.get(cfg.api.BASE_URL+'/athlete/activities',
                          params={'per_page': 200, 'after': from_, 'before': to_})
    res_dict = res.json()
    # extract ids
    ids = [_['id'] for _ in res_dict]
    return set(ids)


def get_activity_metadata(cfg: DictConfig, id: int) -> Dict[str, Any]:
    """query metadata from strava api for a given

    Args:
        cfg (DictConfig): [description]
        id (int): activity id

    Returns:
        Dict[str, Any]: activity data
    """
    # get metadata
    with MySession(cfg) as session:
        meta = session.get(cfg.api.BASE_URL+f'/activities/{id}')
    meta_dict = meta.json()
    # save to dict
    res = dict()
    for col in cfg.api.TO_GET:
        res[col] = meta_dict.get(col)
    res['gear'] = meta_dict['gear'].get(
        'name') if 'gear' in meta_dict else None
    res['id'] = id
    # convert date strings to python datetime
    if res['start_date_local'] is not None:
        res['start_date_local'] = pd.to_datetime(res['start_date_local'])\
            .to_pydatetime()
    # write to db if configured
    if cfg.TO_DB:
        to_db = pd.DataFrame(res, index=[0])
        to_db['last_update'] = save_datetime_now()
        with sqlite3.connect(call(cfg.DB)) as con:
            to_db.to_sql('ACTIVITIES_META', con=con, if_exists='append',
                         index=False, index_label='id')
    # sleep to net get kicked form api
    time.sleep(cfg.api.SLEEP)
    return res


def get_activity_rawdata(cfg: DictConfig, id: int) -> pd.DataFrame:
    """query rawdata from strava api for a given id

    Args:
        cfg (DictConfig): configuration
        id (int): activity id

    Returns:
        pd.DataFrame: activity rawdata
    """
    # get streams from activity
    with MySession(cfg) as session:
        stream = session.get(
            cfg.api.BASE_URL+f'/activities/{id}/streams',
            params={'keys': ','.join(cfg.api.STREAMS)})
    activity = dict()
    found = list()
    # iterate over values
    for values in stream.json():
        activity[values['type']] = values['data']
        found.append(values['type'])
    # make df from dict
    res_df = pd.DataFrame(activity)
    # extract lat and long if available
    try:
        res_df['lat'] = res_df['latlng'].apply(lambda x: x[0])
        res_df['long'] = res_df['latlng'].apply(lambda x: x[-1])
    except KeyError:
        res_df['lat'], res_df['long'] = np.nan, np.nan
    # check if columns missing - if so set as nan
    missings = set(cfg.api.STREAMS) - set(found)
    if missings:
        for missing in missings:
            res_df[missing] = np.nan
    # save id
    res_df['id'] = id
    # delte old latlng
    if 'latlng' in res_df:
        del res_df['latlng']
    # write to DB if configured
    if cfg.TO_DB:
        res_df['last_update'] = save_datetime_now()
        with sqlite3.connect(call(cfg.DB)) as con:
            res_df.to_sql('ACTIVITIES_RAW', con=con, if_exists='append',
                          index=False, index_label='id')
    time.sleep(cfg.api.SLEEP)
    return res_df
