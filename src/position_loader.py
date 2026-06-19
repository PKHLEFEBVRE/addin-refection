import logging
import dateutil.parser
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from portfolio import Portfolio
from position import Position
from utils import parse_xml_file, get_lines_from_csv

logger = logging.getLogger(__name__)

def get_positions_by_date_from_xml_file(dt: datetime, fund: Portfolio) -> Dict[str, Position]:
    """Stub logic for XML position parsing, as specific XML schema is not provided."""
    logger.warning("XML parsing is not fully implemented due to lack of schema.")
    return {}

def get_positions_by_date_from_infin_csv_file(path: str, dt: datetime, fund: Portfolio) -> Dict[str, Position]:
    records = get_lines_from_csv(path, delimiter=';')
    if not records:
        logger.error(f"No inventory found at: {path}")
        return {}

    positions: Dict[str, Position] = {}

    for row in records:
        pos_id = str(row.get("SecurityId", row.get("ISIN", ""))).strip()
        if not pos_id:
            continue

        def get_float(k: str) -> float:
            val = str(row.get(k, ""))
            if val:
                try:
                    return float(val.replace(',', '.'))
                except ValueError:
                    pass
            return 0.0

        pos = Position(
            pos_id=pos_id,
            fund=str(row.get("Fund", fund.name)),
            account=str(row.get("Account", "")),
            dt=dt,
            name=str(row.get("Name", "")),
            isin=str(row.get("ISIN", "")),
            ticker=str(row.get("Ticker", "")),
            qty=get_float("Quantity"),
            price=get_float("Price"),
            ccy=str(row.get("Currency", "")),
            fx=get_float("FX"),
            quote_in_pct=get_float("QuoteInPct"),
            amount_base_cur=get_float("AmountBaseCur")
        )

        positions[pos_id] = pos

    return positions
