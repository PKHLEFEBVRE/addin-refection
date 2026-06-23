from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from position import Position

@dataclass
class Portfolio:
    fund_type: str = ""
    fund_id: str = ""
    symbol: str = ""
    name: str = ""
    currency: str = ""
    creation_date: Optional[datetime] = None
    inception_date: Optional[datetime] = None
    closing_date: Optional[datetime] = None
    active: bool = False
    custodian: str = ""
    mandate_type: str = ""
    account_type: str = ""
    life_insurer: str = ""
    life_insurer_product: str = ""
    profile: str = ""
    model: str = ""
    manager: str = ""
    srri: str = ""
    sri: str = ""
    via: str = ""

    # Internal computational properties
    cash_and_treso: float = 0.0
    aum: float = 0.0
    exposure_limits: Dict[str, Any] = field(default_factory=dict)
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: Dict[str, Position] = field(default_factory=dict)

    _equity_delta: float = field(default=0.0, init=False)
    _equity_delta_computed: bool = field(default=False, init=False)

    def set_trades(self, trades_dict: Dict[str, Position]) -> None:
        if trades_dict is not None:
            self.trades = trades_dict

    def get_positions_with_trades(self) -> Dict[str, Position]:
        sim_positions = {k: pos.clone() for k, pos in self.positions.items()}
        total_trade_cost = sum(t.amount_base_cur for k, t in self.trades.items() if k != "10")

        for key, trade in self.trades.items():
            if trade.pos_id in sim_positions:
                new_pos = sim_positions[trade.pos_id]
                new_pos.qty += trade.qty
                new_pos.amount_base_cur += trade.amount_base_cur
            else:
                sim_positions[trade.pos_id] = trade.clone()

        if "10" in sim_positions:
            sim_positions["10"].amount_base_cur -= total_trade_cost
        else:
            print(f"Warning: Cash position '10' not found in portfolio {self.name}")

        sim_aum = sum(pos.amount_base_cur for pos in sim_positions.values())
        if sim_aum != 0:
            for pos in sim_positions.values():
                pos.weight = pos.amount_base_cur / sim_aum

        return sim_positions

    def get_computed_equity_delta(self) -> float:
        if self._equity_delta_computed:
            return self._equity_delta

        self._equity_delta = sum(
            pos.weight * pos.pos_instrument.equity_delta
            for pos in self.positions.values() if pos.pos_instrument
        )
        self._equity_delta_computed = True
        return self._equity_delta

    def get_positions(self, dt: datetime) -> Dict[str, Position]:
        import data
        if self.positions:
            return self.positions

        inventory_id = self.fund_id or self.name

        if inventory_id:
            self.positions = data.get_inventory(dt, self.fund_id, self.name)
            self.aum = sum(pos.amount_base_cur for pos in self.positions.values())

            if self.aum != 0:
                for pos in self.positions.values():
                    pos.weight = pos.amount_base_cur / self.aum

        self._equity_delta_computed = False
        return self.positions

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Portfolio":
        import pandas as pd
        import dateutil.parser

        def get_str(k: str) -> str:
            val = data.get(k)
            return str(val).replace('"', '').strip() if pd.notna(val) and val != "" else ""

        def get_bool(k: str) -> bool:
            return str(get_str(k)).lower() == 'true'

        port = cls(
            fund_type=get_str("Type"),
            fund_id=get_str("Id"),
            symbol=get_str("Symbol"),
            name=get_str("Name"),
            currency=get_str("Currency"),
            active=get_bool("Active"),
            custodian=get_str("Custodian"),
            mandate_type=get_str("Mandate Type"),
            account_type=get_str("Account Type"),
            life_insurer=get_str("Life Insurer"),
            life_insurer_product=get_str("Life Insurer Product"),
            profile=get_str("Profile"),
            model=get_str("Model"),
            manager=get_str("Manager"),
            srri=get_str("SRRI"),
            sri=get_str("SRI"),
            via=get_str("Via")
        )

        for date_field, attr_name in [
            ("Creation Date", "creation_date"),
            ("Inception Date", "inception_date"),
            ("Closing Date", "closing_date")
        ]:
            val = get_str(date_field)
            if val:
                try:
                    setattr(port, attr_name, dateutil.parser.parse(val))
                except Exception:
                    pass

        return port
