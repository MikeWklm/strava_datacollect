from strava_datacollect.utils.data import TokenStatus
import time
import hydra
from omegaconf import DictConfig
import schedule
from strava_datacollect.strava_auth import (fetch_token, get_response_url, get_token_status,
                                            refresh_token)
from strava_datacollect.strava_query import (initialize_database,
                                             update_meta, update_raw)
from strava_datacollect.utils.base import do_only_once


fetch_token_once = do_only_once(fetch_token)


@hydra.main(config_path='config', config_name='config')
def main(cfg: DictConfig):
    """main method for this application

    schedules different activities:
    make oauth if no token available (once)
    refresh token of token expired (once)
    initialize the database (once)
    hourly query new meta and rawdata

    Args:
        cfg (DictConfig): configuration
    """
    token_status = get_token_status(cfg)
    if token_status == TokenStatus.NO_TOKEN:
        cfg.api.AUTH_RESPONSE = get_response_url(cfg)
        schedule.every().second.do(fetch_token_once, cfg)
    elif token_status == TokenStatus.EXPIRED:
        refresh_token(cfg)
    schedule.every().second.do(initialize_database, cfg)
    schedule.every(6).hours.do(refresh_token, cfg)
    schedule.every(1).hours.do(update_meta, cfg)
    schedule.every(1).hours.do(update_raw, cfg)
    while True:
        schedule.run_pending()
        time.sleep(1)
