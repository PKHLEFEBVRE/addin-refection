from datetime import datetime
from instrument import Instrument

class Position:
    def __init__(self):
        self.pos_id: str = ""
        self.fund: str = ""
        self.account: str = ""
        self.dt: datetime = None
        self.name: str = ""
        self.isin: str = ""
        self.ticker: str = ""
        self.qty: float = 0.0
        self.price: float = 0.0
        self.ccy: str = ""
        self.fx: float = 0.0

        self.quote_in_pct: float = 0.0
        self.amount_base_cur: float = 0.0
        self.weight: float = 0.0

        self.pos_instrument: Instrument = None

    def clone(self) -> 'Position':
        p = Position()
        p.pos_id = self.pos_id
        p.fund = self.fund
        p.account = self.account
        p.dt = self.dt
        p.name = self.name
        p.isin = self.isin
        p.ticker = self.ticker
        p.qty = self.qty
        p.price = self.price
        p.ccy = self.ccy
        p.fx = self.fx

        p.quote_in_pct = self.quote_in_pct
        p.amount_base_cur = self.amount_base_cur
        p.weight = self.weight

        p.pos_instrument = self.pos_instrument

        return p
