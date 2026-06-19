from typing import Dict, Any, Tuple
from portfolio import Portfolio
from position import Position
from instrument import Instrument
from portfolio_factory import PortfolioFactory

class PositionsReportsFactory:
    @staticmethod
    def get_exposure(port: Portfolio, key1: str, key2: str = "") -> Dict[str, float]:
        exposure: Dict[str, float] = {}

        if not port.positions:
            return exposure

        for pos in port.positions.values():
            inst = pos.pos_instrument

            val1 = PositionsReportsFactory._get_value_for_exposure(pos, inst, key1)

            if key2:
                val2 = PositionsReportsFactory._get_value_for_exposure(pos, inst, key2)
                composite_key = f"{val1}|{val2}"
            else:
                composite_key = val1

            weight = pos.weight

            if composite_key in exposure:
                exposure[composite_key] += weight
            else:
                exposure[composite_key] = weight

        return exposure

    @staticmethod
    def _get_value_for_exposure(pos: Position, inst: Instrument, key: str) -> str:
        # Check instrument attributes first
        if inst is not None:
            if hasattr(inst, key) or hasattr(inst, PositionsReportsFactory._to_snake_case(key)):
                val = getattr(inst, key, getattr(inst, PositionsReportsFactory._to_snake_case(key), None))
                if val is not None:
                    return str(val)

        # Then check position attributes
        if hasattr(pos, key) or hasattr(pos, PositionsReportsFactory._to_snake_case(key)):
            val = getattr(pos, key, getattr(pos, PositionsReportsFactory._to_snake_case(key), None))
            if val is not None:
                return str(val)

        return "N/A"

    @staticmethod
    def _to_snake_case(name: str) -> str:
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def get_aggregated_exposure(portfolios: Dict[str, Portfolio], key1: str, key2: str = "") -> Tuple[Dict[str, Dict[str, float]], Dict[str, str]]:
        exposure_dicts: Dict[str, Dict[str, float]] = {}
        unique_keys: Dict[str, str] = {}

        for port_key, port in portfolios.items():
            exp_dict = PositionsReportsFactory.get_exposure(port, key1, key2)
            exposure_dicts[port_key] = exp_dict

            for exp_key in exp_dict.keys():
                if exp_key not in unique_keys:
                    unique_keys[exp_key] = exp_key

        return exposure_dicts, unique_keys

    @staticmethod
    def generate_diff_portfolios(portfolios: Dict[str, Portfolio], benchmarks: Dict[str, Portfolio]) -> Dict[str, Portfolio]:
        diff_portfolios: Dict[str, Portfolio] = {}

        for key, port in portfolios.items():
            if key in benchmarks:
                bench = benchmarks[key]
                diff_port = PortfolioFactory.create_diff_portfolio(port, bench)
                diff_portfolios[diff_port.name] = diff_port

        return diff_portfolios

    @staticmethod
    def get_exposure_report(portfolios: Dict[str, Portfolio], key1: str, key2: str = "") -> list:
        exp_dicts, keys = PositionsReportsFactory.get_aggregated_exposure(portfolios, key1, key2)

        # Simple cross-tabulation table equivalent to TurnExposureDictsToTable
        # Table output format: Fund names in first col, Exposure keys in header row
        headers = ["Fund"] + list(keys.keys())
        table = [headers]

        for port_key, exp_dict in exp_dicts.items():
            row = [port_key]
            for k in keys.keys():
                row.append(exp_dict.get(k, 0.0))
            table.append(row)

        return table
