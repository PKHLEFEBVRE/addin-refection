from datetime import datetime
from typing import Dict

class Instrument:
    def __init__(self):
        self.instrument_id: str = ""
        self.symbol: str = ""
        self.name: str = ""
        self.isin: str = ""
        self.ticker: str = ""

        self.ccy: str = ""
        self.geography: str = ""
        self.country: str = ""
        self.asset_class: str = ""
        self.category: str = ""
        self.sub_category: str = ""
        self.exchange: str = ""

        self.equity_delta: float = 0.0
        self.guaranteed_capital: float = 0.0
        self.quote_in_pct: bool = False

        self.last_close: float = 0.0
        self.last_close_date: datetime = None

        self.min_rating: str = ""
        self.agencies_ratings: Dict[str, str] = {}

        self.issuer: str = ""
        self.issuer_country: str = ""
        self.issuer_lt_rating_sp: str = ""

        self.man_co: str = ""
        self.is_fia: bool = False

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
            if r in rating_scale:
                if rating_scale[r] > worst_score:
                    worst_score = rating_scale[r]
                    worst_rating = r

        self.min_rating = worst_rating
