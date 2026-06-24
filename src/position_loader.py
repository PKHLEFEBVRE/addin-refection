import logging
import pandas as pd
from datetime import datetime
from typing import Dict
from portfolio import Portfolio
from position import Position

logger = logging.getLogger(__name__)

def _exceptional_adjustments(pos: Position) -> None:
    if pos.isin == "XS2772970781" and pos.fund == "70598445":
        pos.qty = 0.0
    if pos.isin == "XS0461632811" and pos.fund == "70598445":
        pos.qty = 0.0

def get_positions_by_date_from_xml_file(dt: datetime, fund: Portfolio) -> Dict[str, Position]:
    """Stub logic for XML position parsing, as specific XML schema is not provided."""
    logger.warning("XML parsing is not fully implemented due to lack of schema.")
    return {}

def get_positions_by_date_from_infin_csv_file(path: str, dt: datetime, fund: Portfolio) -> Dict[str, Position]:
    try:
        df = pd.read_csv(path, sep=';', header=None, encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to read CSV file at {path}: {str(e)}")
        return {}

    if df.empty:
        logger.error(f"No inventory found at: {path}")
        return {}

    import data
    instruments = data.get_instruments(dt, by_infin_id=True)
    positions: Dict[str, Position] = {}

    for _, row in df.iterrows():
        try:
            pos_id_raw = str(row.iloc[1]).strip()
        except IndexError:
            continue

        if not pos_id_raw:
            continue

        def get_str(index: int) -> str:
            try:
                val = row.iloc[index]
                return str(val).replace('"', '').strip() if pd.notna(val) else ""
            except IndexError:
                return ""

        def get_float(index: int, default: float = 0.0) -> float:
            val = get_str(index)
            if not val:
                return default
            try:
                return float(val.replace(',', '.'))
            except ValueError:
                return default

        account = get_str(11)
        name = get_str(2)
        isin = get_str(3)
        ticker = get_str(9)
        qty = get_float(5)
        price = get_float(6, default=100.0)
        ccy = get_str(7)
        fx = get_float(10)

        fund_id = fund.fund_id or fund.name

        if name != ccy or (name == ccy and (account == fund_id or "main" in account.lower())):
            pos_id = pos_id_raw
        else:
            pos_id = f"{pos_id_raw} {account}"

        pos_instrument = instruments.get(pos_id_raw)

        quote_in_pct_factor = 1.0
        if pos_instrument and getattr(pos_instrument, "quote_in_pct", False):
            quote_in_pct_factor = 0.01

        pos = Position(
            pos_id=pos_id,
            fund=fund_id,
            account=account,
            dt=dt,
            name=name,
            isin=isin,
            ticker=ticker,
            qty=qty,
            price=price,
            ccy=ccy,
            fx=fx,
            quote_in_pct_factor=quote_in_pct_factor,
            pos_instrument=pos_instrument
        )

        _exceptional_adjustments(pos)

        pos.amount_base_cur = pos.qty * pos.price * pos.fx * pos.quote_in_pct_factor

        positions[pos_id] = pos

    return positions
