from collections import defaultdict
from typing import Dict, Tuple, List, Any
from portfolio import Portfolio
from position import Position
from instrument import Instrument
from portfolio_loader import create_diff_portfolio

def get_exposure(port: Portfolio, key1: str, key2: str = "") -> Dict[str, float]:
    exposure: Dict[str, float] = defaultdict(float)

    for pos in port.positions.values():
        inst = pos.pos_instrument

        val1 = _get_value_for_exposure(pos, inst, key1)
        composite_key = f"{val1}|{_get_value_for_exposure(pos, inst, key2)}" if key2 else val1

        exposure[composite_key] += pos.weight

    return dict(exposure)

def _get_value_for_exposure(pos: Position, inst: Instrument, key: str) -> str:
    snake_key = _to_snake_case(key)

    if inst and (hasattr(inst, key) or hasattr(inst, snake_key)):
        val = getattr(inst, key, getattr(inst, snake_key, None))
        if val is not None:
            return str(val)

    if hasattr(pos, key) or hasattr(pos, snake_key):
        val = getattr(pos, key, getattr(pos, snake_key, None))
        if val is not None:
            return str(val)

    return "N/A"

def _to_snake_case(name: str) -> str:
    import re
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)).lower()

def get_aggregated_exposure(portfolios: Dict[str, Portfolio], key1: str, key2: str = "") -> Tuple[Dict[str, Dict[str, float]], List[str]]:
    exposure_dicts = {port_key: get_exposure(port, key1, key2) for port_key, port in portfolios.items()}
    unique_keys = list({exp_key for exp_dict in exposure_dicts.values() for exp_key in exp_dict.keys()})

    return exposure_dicts, unique_keys

def generate_diff_portfolios(portfolios: Dict[str, Portfolio], benchmarks: Dict[str, Portfolio]) -> Dict[str, Portfolio]:
    return {
        create_diff_portfolio(port, benchmarks[key]).name: create_diff_portfolio(port, benchmarks[key])
        for key, port in portfolios.items() if key in benchmarks
    }

def get_exposure_report(portfolios: Dict[str, Portfolio], key1: str, key2: str = "") -> List[List[Any]]:
    exp_dicts, keys = get_aggregated_exposure(portfolios, key1, key2)

    table = [["Fund"] + keys]
    for port_key, exp_dict in exp_dicts.items():
        table.append([port_key] + [exp_dict.get(k, 0.0) for k in keys])

    return table
