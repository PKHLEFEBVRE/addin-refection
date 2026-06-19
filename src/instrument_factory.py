import pandas as pd
import logging
from typing import Dict, Any, List
from instrument import Instrument
from factories import ExcelFactory

logger = logging.getLogger(__name__)

class InstrumentFactory:
    @staticmethod
    def get_instruments_from_file(path: str, by_infin_id: bool) -> Dict[str, Any]:
        lines = ExcelFactory.get_lines_from_excel_file(path, header=True)
        if not lines:
            logger.error(f"No referential found at: {path}\nPlease perform referential extraction.")
            return {}

        instruments: Dict[str, Any] = {}

        # In VBA array limits start at 1 or LBound, here we know row 0 is headers
        columns_dict = InstrumentFactory._create_columns_dict_from_inventory(lines[0])

        for line in lines[1:]:
            # Use columns_dict safely
            asset_class_idx = columns_dict.get("Asset Class")
            if asset_class_idx is None or asset_class_idx >= len(line):
                continue

            asset_class = str(line[asset_class_idx]).lower()

            key = ""
            if by_infin_id:
                idx = columns_dict.get("SecurityId")
                if idx is not None and idx < len(line):
                    key = str(line[idx])
            elif asset_class == "cash":
                idx = columns_dict.get("Name")
                if idx is not None and idx < len(line):
                    key = str(line[idx])
            else:
                idx = columns_dict.get("Bloomberg Ticker")
                if idx is not None and idx < len(line):
                    key = str(line[idx]).upper()

            if key and asset_class:
                inst = InstrumentFactory.create_instrument(line, columns_dict)

                if by_infin_id:
                    instruments[key] = inst
                else:
                    if asset_class not in instruments:
                        instruments[asset_class] = {}

                    if inst.name.lower() != "a supprimer":
                        if key not in instruments[asset_class]:
                            instruments[asset_class][key] = {}

                        if inst.isin in instruments[asset_class][key]:
                            logger.warning(f"DATABASE WARNING - 2 instrument with identical isin and ticker found: {inst.isin} - {inst.ticker}")
                        else:
                            instruments[asset_class][key][inst.isin] = inst

        return instruments

    @staticmethod
    def _create_columns_dict_from_inventory(header_row: List[Any]) -> Dict[str, int]:
        columns_dict = {}
        for i, col_name in enumerate(header_row):
            columns_dict[str(col_name)] = i
        return columns_dict

    @staticmethod
    def create_instrument(line: List[Any], columns_dict: Dict[str, int]) -> Instrument:
        inst = Instrument()

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

        inst.instrument_id = get_val("SecurityId")
        inst.symbol = get_val("Infin Symbol")
        inst.name = get_val("Name")
        inst.isin = get_val("ISIN")
        inst.ticker = get_val("Bloomberg Ticker")

        inst.ccy = get_val("Currency")
        inst.geography = get_val("Geography")
        inst.country = get_val("Country")
        inst.asset_class = get_val("Asset Class")
        inst.category = get_val("Category")
        inst.sub_category = get_val("Sub Category")
        inst.exchange = get_val("Exchange")

        inst.equity_delta = get_float("Delta")
        inst.guaranteed_capital = get_float("Custom Property-Capital Guaranteed")

        inst.last_close = get_float("Close")

        close_date_str = get_val("Close_Date")
        if close_date_str:
            import dateutil.parser
            try:
                inst.last_close_date = dateutil.parser.parse(close_date_str)
            except Exception:
                pass

        sp_rating = get_val("BondRatingSP")
        if sp_rating: inst.agencies_ratings["SP"] = sp_rating

        fitch_rating = get_val("BondRatingFitch")
        if fitch_rating: inst.agencies_ratings["Fitch"] = fitch_rating

        moody_rating = get_val("BondRatingMoody")
        if moody_rating: inst.agencies_ratings["Moodys"] = moody_rating

        inst.issuer = get_val("Issuer")
        inst.issuer_country = get_val("Issuer Country")
        inst.issuer_lt_rating_sp = get_val("IssuerLTRatingSP")

        inst.man_co = get_val("ManCo")

        fia_val = get_val("FIA")
        inst.is_fia = str(fia_val).lower() == 'true' if fia_val else False

        quote_pct_val = get_val("Quoted in percent")
        inst.quote_in_pct = str(quote_pct_val).lower() == 'true' if quote_pct_val else False

        inst.compute_min_rating()

        return inst
