import logging
from datetime import datetime
from typing import Dict, Any
from functools import lru_cache

import instrument_loader
import portfolio_loader
import position_loader
from configuration import Configuration

logger = logging.getLogger(__name__)

_config = Configuration()

@lru_cache(maxsize=128)
def get_inventory(dt: datetime, fund_id: str, fund_name: str) -> Dict[str, Any]:
    ident = fund_id or fund_name

    try:
        from portfolio import Portfolio
        dummy_port = Portfolio(name=fund_name, creation_date=datetime(1970,1,1), inception_date=datetime(1970,1,1))

        if ident in _config.funds_through_xml:
            positions = position_loader.get_positions_by_date_from_xml_file(dt, dummy_port)
        else:
            path = _config.create_inventory_csv_path(dt, ident)
            positions = position_loader.get_positions_by_date_from_infin_csv_file(path, dt, dummy_port)

        if not positions:
            logger.debug(f"cobDate = {dt} with no position found in inventory of fund {ident}")
        else:
            logger.debug(f"cobDate = {dt} with {len(positions)} positions found in inventory of fund {ident}")

        return positions
    except Exception as e:
        logger.error(f"An error occurred on fund {ident} on date {dt}.\n{str(e)}")
        return {}

@lru_cache(maxsize=32)
def get_instruments(dt: datetime, by_infin_id: bool = False) -> Dict[str, Any]:
    path = _config.create_instruments_referential_path(dt)
    instruments = instrument_loader.get_instruments_from_file(path, by_infin_id)

    if not instruments:
        logger.debug(f"cobDate = {dt} with no instruments found.")
    else:
        log_type = "instruments" if by_infin_id else "asset classes"
        logger.debug(f"cobDate = Referential {dt} with {len(instruments)} {log_type} found.")

    return instruments

@lru_cache(maxsize=32)
def get_portfolios(dt: datetime) -> Dict[str, Any]:
    path = _config.create_portfolios_referential_path(dt)
    portfolios = portfolio_loader.get_portfolios_from_file(path, dt)

    if not portfolios:
        logger.debug(f"cobDate = {dt} with no portfolios found.")
    else:
        logger.debug(f"cobDate = Referential {dt} with {len(portfolios)} portfolios found.")

    return portfolios

def clear_cache() -> None:
    get_inventory.cache_clear()
    get_instruments.cache_clear()
    get_portfolios.cache_clear()
    logger.debug("Caches cleared.")

def get_configuration() -> Configuration:
    return _config
