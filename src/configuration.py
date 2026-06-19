# Dummy Configuration class as it was referenced in referential.py and data.py but code wasn't completely provided in texts
from datetime import datetime
from typing import Dict

class Configuration:
    def __init__(self):
        self.funds_through_xml: Dict[str, str] = {}
        self.global_money_market_isin: str = ""

    def create_inventory_csv_path(self, dt: datetime, fund_id: str) -> str:
        # Stub implementation
        return f"inventory_{fund_id}_{dt.strftime('%Y%m%d')}.csv"

    def create_instruments_referential_path(self, dt: datetime) -> str:
        # Stub implementation
        return f"instruments_{dt.strftime('%Y%m%d')}.xlsx"

    def create_portfolios_referential_path(self, dt: datetime) -> str:
        # Stub implementation
        return f"portfolios_{dt.strftime('%Y%m%d')}.xlsx"
