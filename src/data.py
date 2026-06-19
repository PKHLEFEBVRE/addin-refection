import logging
from datetime import datetime
from typing import Dict, Any

from referential import Referential

logger = logging.getLogger(__name__)

# Singleton instance
_the_referential_instance = Referential()

def get_referential() -> Referential:
    global _the_referential_instance
    if _the_referential_instance is None:
        logger.debug("Creation of new instance of Referential")
        _the_referential_instance = Referential()
    return _the_referential_instance

def reset_singleton() -> None:
    global _the_referential_instance
    _the_referential_instance = None

def get_inventory(dt: datetime, fund: Any) -> Dict[str, Any]:
    try:
        ref = get_referential()
        positions = ref.get_inventory_infin(dt, fund)

        if not positions:
            logger.debug(f"cobDate = {dt} with no position found in inventory of fund {fund.name}")
        else:
            logger.debug(f"cobDate = {dt} with {len(positions)} positions found in inventory of fund {fund.name}")

        return positions
    except Exception as e:
        logger.error(f"An error occurred on fund {fund.name} on date {dt}.\n{str(e)}")
        return {}

def get_instruments(dt: datetime, by_infin_id: bool = False) -> Dict[str, Any]:
    ref = get_referential()
    instruments = ref.get_instruments_infin_by_key(dt, by_infin_id)

    if not instruments:
        logger.debug(f"cobDate = {dt} with no instruments found.")
    else:
        if by_infin_id:
            logger.debug(f"cobDate = Referential {dt} with {len(instruments)} instruments found.")
        else:
            logger.debug(f"cobDate = Referential {dt} with {len(instruments)} asset classes found.")

    return instruments

def get_portfolios(dt: datetime) -> Dict[str, Any]:
    ref = get_referential()
    portfolios = ref.get_portfolios_infin_by_key(dt)

    if not portfolios:
        logger.debug(f"cobDate = {dt} with no portfolios found.")
    else:
        logger.debug(f"cobDate = Referential {dt} with {len(portfolios)} portfolios found.")

    return portfolios

def get_configuration() -> Any:
    ref = get_referential()
    return ref.get_configuration()
