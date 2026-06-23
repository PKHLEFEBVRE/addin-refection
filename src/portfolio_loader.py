import logging
import dateutil.parser
import pandas as pd
from datetime import datetime
from typing import Dict
from portfolio import Portfolio
from utils import get_lines_from_excel_file

logger = logging.getLogger(__name__)

def get_portfolios_from_file(path: str, dt: datetime) -> Dict[str, Portfolio]:
    records = get_lines_from_excel_file(path)
    if not records:
        logger.error(f"No portfolio referential found at:\n\n{path}")
        return {}

    portfolios: Dict[str, Portfolio] = {}

    for row in records:
        key = str(row.get("Id", "")).strip() or str(row.get("Name", "")).strip()

        if key:
            if key not in portfolios:
                portfolios[key] = Portfolio.from_dict(row)
            else:
                logger.debug(f"Duplicate portfolio key: {key}")

    return portfolios

def load_positions_for_type(portfolios: Dict[str, Portfolio], type_filter: str, dt: datetime) -> None:
    type_filter_lower = type_filter.lower()
    for port in portfolios.values():
        if port.fund_type.lower() == type_filter_lower:
            port.get_positions(dt)

def create_diff_portfolio(port: Portfolio, bench: Portfolio) -> Portfolio:
    diff_port = Portfolio(
        creation_date=port.creation_date,
        inception_date=port.inception_date,
        name=f"{port.name} vs {bench.name}",
        fund_type="Difference",
        mandate_type=port.mandate_type,
        currency=port.currency
    )

    diff_port.positions = {k: v.clone() for k, v in port.positions.items()}

    for b_pos in bench.positions.values():
        if b_pos.pos_id in diff_port.positions:
            diff_port.positions[b_pos.pos_id].weight -= b_pos.weight
        else:
            new_pos = b_pos.clone()
            new_pos.weight = -b_pos.weight
            diff_port.positions[new_pos.pos_id] = new_pos

    return diff_port

def enrich_portfolios_from_dashboard(portfolios: Dict[str, Portfolio], path: str) -> None:
    records = get_lines_from_excel_file(path)
    if not records:
        return

    found_portfolios = set()

    for row in records:
        key = str(row.get("Id", "")).strip() or str(row.get("Name", "")).strip()
        port = portfolios.get(key)

        if not port:
            key_lower = key.lower()
            port = next((p for p in portfolios.values() if key_lower in (p.fund_id.lower(), p.name.lower())), None)

        if port:
            found_portfolios.add(port.fund_id)
            found_portfolios.add(port.name)

            def get_str(col: str) -> str:
                val = row.get(col)
                return str(val) if pd.notna(val) else ""

            def get_bool(k: str) -> bool:
                return str(get_str(k)).lower() == 'true'

            if fund_type := get_str("Type"): port.fund_type = fund_type
            if symbol := get_str("Symbol"): port.symbol = symbol
            if currency := get_str("Currency"): port.currency = currency
            port.active = get_bool("Active")
            if custodian := get_str("Custodian"): port.custodian = custodian
            if mandate_type := get_str("Mandate Type"): port.mandate_type = mandate_type
            if account_type := get_str("Account Type"): port.account_type = account_type
            if life_insurer := get_str("Life Insurer"): port.life_insurer = life_insurer
            if life_insurer_product := get_str("Life Insurer Product"): port.life_insurer_product = life_insurer_product
            if profile := get_str("Profile"): port.profile = profile
            if model := get_str("Model"): port.model = model
            if manager := get_str("Manager"): port.manager = manager
            if srri := get_str("SRRI"): port.srri = srri
            if sri := get_str("SRI"): port.sri = sri
            if via := get_str("Via"): port.via = via

            for date_field, attr_name in [
                ("Creation Date", "creation_date"),
                ("Inception Date", "inception_date"),
                ("Closing Date", "closing_date")
            ]:
                if val := get_str(date_field):
                    try:
                        setattr(port, attr_name, dateutil.parser.parse(val))
                    except Exception:
                        pass

    missing = [f"- {p.name} ({p.fund_id})" for p in portfolios.values() if p.fund_id not in found_portfolios and p.name not in found_portfolios]

    if missing:
        msg = "CRITICAL ERROR: The following portfolios are missing from the Dashboard sheet.\n"
        msg += "Please update the dashboard and retry.\n\n"
        msg += "\n".join(missing)
        logger.error(msg)
        raise Exception("Portfolios missing from Dashboard sheet.")
