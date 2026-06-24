import logging
from typing import Dict, Any
from instrument import Instrument
from utils import get_lines_from_excel_file

logger = logging.getLogger(__name__)

def get_instruments_from_file(path: str, by_infin_id: bool) -> Dict[str, Any]:
    records = get_lines_from_excel_file(path)
    if not records:
        logger.error(f"No referential found at: {path}\nPlease perform referential extraction.")
        return {}

    instruments: Dict[str, Any] = {}

    for row in records:
        asset_class = str(row.get("Asset Class", "")).lower()
        if not asset_class:
            continue

        if by_infin_id:
            key = str(row.get("SecurityId", ""))
        elif asset_class == "cash":
            key = str(row.get("Name", ""))
        else:
            key = str(row.get("Bloomberg Ticker", "")).upper()

        if key:
            inst = Instrument.from_dict(row)
            if by_infin_id:
                instruments[key] = inst
            else:
                if inst.name.lower() != "a supprimer":
                    instruments.setdefault(asset_class, {}).setdefault(key, {})

                    if inst.isin in instruments[asset_class][key]:
                        logger.warning(f"DATABASE WARNING - 2 instruments with identical ISIN and ticker found: {inst.isin} - {inst.ticker}")
                    else:
                        instruments[asset_class][key][inst.isin] = inst

    return instruments
