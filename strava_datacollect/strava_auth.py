import getpass
import os
import sqlite3
from datetime import datetime
from strava_datacollect.utils.data import TokenStatus, table_exists
from typing import Any, Dict, List

import hydra
import pandas as pd
from hydra.utils import call
from omegaconf import DictConfig
from requests.sessions import Session
from requests_oauthlib import OAuth2Session

from strava_datacollect.utils.base import save_datetime_now


@hydra.main(config_path='config', config_name='config')
def fetch_token(cfg: DictConfig) -> pd.DataFrame:
    """fetches token from strava api

    Args:
        cfg (DictConfig): configuration

    Returns:
        pd.DataFrame: the updated token
    """
    oauth = OAuth2Session(client_id=cfg.api.CLIENT_ID,
                          scope=cfg.api.SCOPE, redirect_uri=cfg.api.REDIRECT_URI)
    token = oauth.fetch_token(cfg.api.TOKEN_EXCHANGE_URL,
                              authorization_response=cfg.api.AUTH_RESPONSE,
                              client_secret=cfg.api.CLIENT_SECRET,
                              include_client_id=True)
    token_df = update_tokens(cfg, token)
    return token_df


@hydra.main(config_path='config', config_name='config')
def get_auth_url(cfg: DictConfig) -> str:
    """get authorization url from strava

    Args:
        cfg (DictConfig): configuration

    Returns:
        str: authorization url
    """
    oauth = OAuth2Session(client_id=cfg.api.CLIENT_ID,
                          scope=cfg.api.SCOPE,
                          redirect_uri=cfg.api.REDIRECT_URI)
    auth_url, _ = oauth.authorization_url(
        cfg.api.OAUTH_BASE_URL, approval_prompt='force')
    return auth_url


@hydra.main(config_path='config', config_name='config')
def get_response_url(cfg: DictConfig) -> str:
    auth_url = get_auth_url(cfg)
    print(f"""
    Please visit {auth_url} and authenticate this application.

    Please paste the URL where you have been redirected to.
    """)
    os.environ['AUTH_RESPONSE'] = getpass.getpass('Reponse URL: ')
    return os.environ['AUTH_RESPONSE']


@hydra.main(config_path='config', config_name='config')
def refresh_token(cfg: DictConfig) -> str:
    """get a new refresh token

    Args:
        cfg (DictConfig): configuration

    Returns:
        str: the updated token
    """
    refresh_token = get_latest(cfg, ['refresh_token'])['refresh_token']
    data = {
        'client_id': cfg.api.CLIENT_ID,
        'client_secret': cfg.api.CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    with MySession(cfg) as session:
        auth = session.post(cfg.api.TOKEN_EXCHANGE_URL, data=data)
    auth_dict = auth.json()
    return update_tokens(cfg, auth_dict)


class MySession:
    def __init__(self, cfg: DictConfig):
        self.cfg = cfg

    def __enter__(self) -> Session:
        auth = get_latest(self.cfg, ['token_type', 'access_token'])
        HEADER = {
            'Authorization': f'{auth["token_type"]} {auth["access_token"]}'}
        self.session = Session()
        self.session.headers.update(HEADER)
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.session.close()


def get_latest(cfg: DictConfig, columns: List[str]) -> Dict[str, Any]:
    columns = ", ".join(columns)
    query = f"""
    SELECT
        {columns}
    FROM
        AUTH_INFO
    WHERE
        user_id = {cfg.api.CLIENT_ID}
    ORDER BY last_update desc
    LIMIT 1;
    """
    with sqlite3.connect(call(cfg.DB)) as con:
        auth = pd.read_sql(query, con)
        auth = auth.iloc[0, :].to_dict()
    return auth


def update_tokens(cfg: DictConfig, token: Dict[str, Any]) -> pd.DataFrame:
    token_dict = dict()
    token_dict['token_type'] = token['token_type']
    token_dict['access_token'] = token['access_token']
    token_dict['refresh_token'] = token['refresh_token']
    token_dict['expires_at'] = datetime.fromtimestamp(token['expires_at'])
    token_dict['last_update'] = save_datetime_now()
    token_dict['user_id'] = cfg.api.CLIENT_ID
    token_df = pd.DataFrame(token_dict, index=[0])
    with sqlite3.connect(call(cfg.DB)) as con:
        token_df.to_sql('AUTH_INFO', con=con, if_exists='append',
                        index=False, index_label='last_update')
    return token_df


@hydra.main(config_path='config', config_name='config')
def get_token_status(cfg: DictConfig) -> TokenStatus:
    with sqlite3.connect(call(cfg.DB)) as con:
        if table_exists(con, 'AUTH_INFO'):
            auth_info = get_latest(cfg, ['expires_at'])
            expire_date = pd.to_datetime(auth_info['expires_at'])
            if expire_date > datetime.now():
                return TokenStatus.ACTIVE
            return TokenStatus.EXPIRED
        return TokenStatus.NO_TOKEN


if __name__ == "__main__":
    get_token_status()
