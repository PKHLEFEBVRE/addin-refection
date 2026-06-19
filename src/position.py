from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional
from instrument import Instrument

@dataclass
class Position:
    pos_id: str = ""
    fund: str = ""
    account: str = ""
    dt: Optional[datetime] = None
    name: str = ""
    isin: str = ""
    ticker: str = ""
    qty: float = 0.0
    price: float = 0.0
    ccy: str = ""
    fx: float = 0.0

    quote_in_pct: float = 0.0
    amount_base_cur: float = 0.0
    weight: float = 0.0

    pos_instrument: Optional[Instrument] = None

    def clone(self) -> 'Position':
        """Creates a shallow copy of the Position."""
        return replace(self)
