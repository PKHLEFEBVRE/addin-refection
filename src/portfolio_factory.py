import logging
import dateutil.parser
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from portfolio import Portfolio
from position import Position
from factories import ExcelFactory

logger = logging.getLogger(__name__)

class PortfolioFactory:
    @staticmethod
    def get_portfolios_from_file(path: str, dt: datetime) -> Dict[str, Portfolio]:
        lines = ExcelFactory.get_lines_from_excel_file(path, header=True)
        if not lines:
            logger.error(f"No portfolio referential found at:\n\n{path}")
            return {}

        portfolios: Dict[str, Portfolio] = {}
        columns_dict = PortfolioFactory._create_columns_dict_from_inventory(lines[0])

        for line in lines[1:]:
            key = ""
            infin_id_idx = columns_dict.get("InfinId")
            if infin_id_idx is not None and infin_id_idx < len(line):
                val = str(line[infin_id_idx]).strip()
                if val: key = val

            if not key:
                name_idx = columns_dict.get("Name")
                if name_idx is not None and name_idx < len(line):
                    val = str(line[name_idx]).strip()
                    if val: key = val

            if key:
                port = PortfolioFactory.create_portfolio(line, columns_dict)

                if key not in portfolios:
                    portfolios[key] = port
                else:
                    logger.debug(f"Duplicate portfolio key: {key}")

        return portfolios

    @staticmethod
    def _create_columns_dict_from_inventory(header_row: List[Any]) -> Dict[str, int]:
        columns_dict = {}
        for i, col_name in enumerate(header_row):
            columns_dict[str(col_name)] = i
        return columns_dict

    @staticmethod
    def create_portfolio(line: List[Any], columns_dict: Dict[str, int]) -> Portfolio:
        port = Portfolio()

        def get_val(key: str) -> str:
            idx = columns_dict.get(key)
            if idx is not None and idx < len(line):
                val = line[idx]
                return str(val).replace('"', '') if pd.notna(val) and val != "" else ""
            return ""

        def get_float(key: str) -> float:
            val = get_val(key)
            if val:
                try:
                    return float(val.replace(',', '.'))
                except ValueError:
                    pass
            return 0.0

        port.name = get_val("Name")
        port.comment = get_val("comment")
        port.infin_id = get_val("InfinId")
        port.insurance_contract = get_val("insuranceContract")
        port.account_name = get_val("accountName")
        port.client = get_val("client")
        port.insurer = get_val("insurer")
        port.custodian = get_val("custodian")
        port.sales = get_val("sales")

        port.fund_type = get_val("Type")
        port.mandat_type = get_val("AccountType")

        port.av_type = get_val("AVType")
        port.ccy = get_val("ccy")
        port.profile = get_val("profile")
        port.composition = get_val("composition")
        port.target_profile = get_val("targetProfile")
        port.target_composition = get_val("targetComposition")
        port.last_computed = get_val("lastComputed")

        creation_date_str = get_val("creationDate")
        if creation_date_str:
            try:
                port.creation_date = dateutil.parser.parse(creation_date_str)
            except Exception:
                pass

        port.cash_and_treso = get_float("CashAndTreso")
        port.aum = get_float("AUM")

        return port

    @staticmethod
    def load_positions_for_type(portfolios: Dict[str, Portfolio], type_filter: str, dt: datetime) -> None:
        for port in portfolios.values():
            if port.fund_type.lower() == type_filter.lower():
                port.get_positions(dt)

    @staticmethod
    def create_diff_portfolio(port: Portfolio, bench: Portfolio) -> Portfolio:
        diff_port = Portfolio()
        diff_port.name = f"{port.name} vs {bench.name}"
        diff_port.fund_type = "Difference"
        diff_port.mandat_type = port.mandat_type
        diff_port.ccy = port.ccy

        if port.positions:
            for p_pos in port.positions.values():
                new_pos = p_pos.clone()
                diff_port.positions[new_pos.pos_id] = new_pos

        if bench.positions:
            for b_pos in bench.positions.values():
                if b_pos.pos_id in diff_port.positions:
                    diff_port.positions[b_pos.pos_id].weight -= b_pos.weight
                else:
                    new_pos = b_pos.clone()
                    new_pos.weight = -b_pos.weight
                    diff_port.positions[new_pos.pos_id] = new_pos

        return diff_port

    @staticmethod
    def enrich_portfolios_from_dashboard(portfolios: Dict[str, Portfolio], path: str) -> None:
        lines = ExcelFactory.get_lines_from_excel_file(path, header=True)
        if not lines or len(lines) < 2:
            return

        headers = PortfolioFactory._create_columns_dict_from_inventory(lines[0])
        found_portfolios: Dict[str, bool] = {}

        for r in range(1, len(lines)):
            line = lines[r]

            key = ""
            infin_id_idx = headers.get("InfinId")
            if infin_id_idx is not None and infin_id_idx < len(line):
                key = str(line[infin_id_idx])
            else:
                acc_name_idx = headers.get("Account name")
                if acc_name_idx is not None and acc_name_idx < len(line):
                    key = str(line[acc_name_idx])

            port = None

            if key in portfolios:
                port = portfolios[key]
            else:
                key_lower = key.lower()
                for p_key, p_val in portfolios.items():
                    if (p_val.infin_id.lower() == key_lower or
                        p_val.account_name.lower() == key_lower or
                        p_val.name.lower() == key_lower):
                        port = p_val
                        break

            if port:
                found_portfolios[port.infin_id] = True
                found_portfolios[port.name] = True

                def get_val(col_name: str) -> str:
                    idx = headers.get(col_name)
                    if idx is not None and idx < len(line):
                        val = line[idx]
                        return str(val) if pd.notna(val) else ""
                    return ""

                client = get_val("Client")
                if client: port.client = client

                creation_date = get_val("Creation date")
                if creation_date:
                    try:
                        port.creation_date = dateutil.parser.parse(creation_date)
                    except Exception:
                        pass

                insurer = get_val("Insurer")
                if insurer: port.insurer = insurer

                custodian = get_val("Custodian")
                if custodian: port.custodian = custodian

                sales = get_val("Sales")
                if sales: port.sales = sales

                account_type = get_val("Account type")
                if account_type: port.mandat_type = account_type

                av_type = get_val("AV Type")
                if av_type: port.av_type = av_type

                ccy = get_val("CCY")
                if ccy: port.ccy = ccy

                profile = get_val("Profile")
                if profile: port.profile = profile

                composition = get_val("Composition")
                if composition: port.composition = composition

                target_profile = get_val("Target Profile")
                if target_profile: port.target_profile = target_profile

                target_composition = get_val("Target Composition")
                if target_composition: port.target_composition = target_composition

        missing_list = []
        for p_obj in portfolios.values():
            if p_obj.infin_id not in found_portfolios and p_obj.name not in found_portfolios:
                missing_list.append(f"- {p_obj.name} ({p_obj.infin_id})")

        if missing_list:
            msg = "CRITICAL ERROR: The following portfolios are missing from the Dashboard sheet.\n"
            msg += "Please update the dashboard and retry.\n\n"
            msg += "\n".join(missing_list)
            logger.error(msg)
            raise Exception("Portfolios missing from Dashboard sheet.")
