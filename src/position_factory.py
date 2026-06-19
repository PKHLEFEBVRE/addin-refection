# Dummy PositionFactory to satisfy referential.py imports
from datetime import datetime
from typing import Dict, Any
from portfolio import Portfolio

class PositionFactory:
    @staticmethod
    def get_positions_by_date_from_xml_file(dt: datetime, fund: Portfolio) -> Dict[str, Any]:
        # Stub implementation
        return {}

    @staticmethod
    def get_positions_by_date_from_infin_csv_file(path: str, dt: datetime, fund: Portfolio) -> Dict[str, Any]:
        # Stub implementation
        return {}
