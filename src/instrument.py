from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class Instrument:
    instrument_id: str = ""
    symbol: str = ""
    name: str = ""
    isin: str = ""
    ticker: str = ""

    ccy: str = ""
    geography: str = ""
    country: str = ""
    asset_class: str = ""
    category: str = ""
    sub_category: str = ""
    exchange: str = ""

    equity_delta: float = 0.0
    guaranteed_capital: float = 0.0
    quote_in_pct: bool = False

    last_close: float = 0.0
    last_close_date: Optional[datetime] = None

    min_rating: str = ""
    agencies_ratings: Dict[str, str] = field(default_factory=dict)

    issuer: str = ""
    issuer_country: str = ""
    issuer_lt_rating_sp: str = ""

    man_co: str = ""
    is_fia: bool = False

    def compute_min_rating(self) -> None:
        if not self.agencies_ratings:
            return

        rating_scale = {
            "AAA": 1, "AA+": 2, "AA": 3, "AA-": 4, "A+": 5, "A": 6, "A-": 7,
            "BBB+": 8, "BBB": 9, "BBB-": 10, "BB+": 11, "BB": 12, "BB-": 13,
            "B+": 14, "B": 15, "B-": 16, "CCC": 17, "CC": 18, "C": 19, "D": 20
        }

        worst_score = 0
        worst_rating = "N/A"

        for agency, rating in self.agencies_ratings.items():
            r = rating.strip().upper()
            if r in rating_scale and rating_scale[r] > worst_score:
                worst_score = rating_scale[r]
                worst_rating = r

        self.min_rating = worst_rating

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Instrument":
        """Creates an Instrument instance from a dictionary (e.g., a pandas row converted to dict)."""
        import pandas as pd
        import dateutil.parser

        def get_str(k: str) -> str:
            val = data.get(k)
            return str(val).replace('"', '').strip() if pd.notna(val) and val != "" else ""

        def get_float(k: str) -> float:
            val = get_str(k)
            if val:
                try:
                    return float(val.replace(',', '.'))
                except ValueError:
                    pass
            return 0.0

        def get_bool(k: str) -> bool:
            return str(get_str(k)).lower() == 'true'

        inst = cls(
            instrument_id=get_str("SecurityId"),
            symbol=get_str("Infin Symbol"),
            name=get_str("Name"),
            isin=get_str("ISIN"),
            ticker=get_str("Bloomberg Ticker"),
            ccy=get_str("Currency"),
            geography=get_str("Geography"),
            country=get_str("Country"),
            asset_class=get_str("Asset Class"),
            category=get_str("Category"),
            sub_category=get_str("Sub Category"),
            exchange=get_str("Exchange"),
            equity_delta=get_float("Delta"),
            guaranteed_capital=get_float("Custom Property-Capital Guaranteed"),
            last_close=get_float("Close"),
            issuer=get_str("Issuer"),
            issuer_country=get_str("Issuer Country"),
            issuer_lt_rating_sp=get_str("IssuerLTRatingSP"),
            man_co=get_str("ManCo"),
            is_fia=get_bool("FIA"),
            quote_in_pct=get_bool("Quoted in percent")
        )

        close_date_str = get_str("Close_Date")
        if close_date_str:
            try:
                inst.last_close_date = dateutil.parser.parse(close_date_str)
            except Exception:
                pass

        if sp := get_str("BondRatingSP"): inst.agencies_ratings["SP"] = sp
        if fitch := get_str("BondRatingFitch"): inst.agencies_ratings["Fitch"] = fitch
        if moodys := get_str("BondRatingMoody"): inst.agencies_ratings["Moodys"] = moodys

        inst.compute_min_rating()
        return inst
