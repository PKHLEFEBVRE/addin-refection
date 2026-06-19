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
        key = str(row.get("InfinId", "")).strip() or str(row.get("Name", "")).strip()

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
        name=f"{port.name} vs {bench.name}",
        fund_type="Difference",
        mandat_type=port.mandat_type,
        ccy=port.ccy
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
        key = str(row.get("InfinId", "")).strip() or str(row.get("Account name", "")).strip()
        port = portfolios.get(key)

        if not port:
            key_lower = key.lower()
            port = next((p for p in portfolios.values() if key_lower in (p.infin_id.lower(), p.account_name.lower(), p.name.lower())), None)

        if port:
            found_portfolios.add(port.infin_id)
            found_portfolios.add(port.name)

            def get_str(col: str) -> str:
                val = row.get(col)
                return str(val) if pd.notna(val) else ""

            if client := get_str("Client"): port.client = client
            if insurer := get_str("Insurer"): port.insurer = insurer
            if custodian := get_str("Custodian"): port.custodian = custodian
            if sales := get_str("Sales"): port.sales = sales
            if acc_type := get_str("Account type"): port.mandat_type = acc_type
            if av_type := get_str("AV Type"): port.av_type = av_type
            if ccy := get_str("CCY"): port.ccy = ccy
            if profile := get_str("Profile"): port.profile = profile
            if comp := get_str("Composition"): port.composition = comp
            if t_prof := get_str("Target Profile"): port.target_profile = t_prof
            if t_comp := get_str("Target Composition"): port.target_composition = t_comp

            if creation_date := get_str("Creation date"):
                try:
                    port.creation_date = dateutil.parser.parse(creation_date)
                except Exception:
                    pass

    missing = [f"- {p.name} ({p.infin_id})" for p in portfolios.values() if p.infin_id not in found_portfolios and p.name not in found_portfolios]

    if missing:
        msg = "CRITICAL ERROR: The following portfolios are missing from the Dashboard sheet.\n"
        msg += "Please update the dashboard and retry.\n\n"
        msg += "\n".join(missing)
        logger.error(msg)
        raise Exception("Portfolios missing from Dashboard sheet.")
