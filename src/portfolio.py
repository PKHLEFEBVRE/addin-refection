from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from position import Position

@dataclass
class Portfolio:
    name: str = ""
    comment: str = ""
    infin_id: str = ""
    insurance_contract: str = ""
    account_name: str = ""
    client: str = ""
    creation_date: Optional[datetime] = None
    insurer: str = ""
    custodian: str = ""
    sales: str = ""
    mandat_type: str = ""
    fund_type: str = ""
    av_type: str = ""
    ccy: str = ""
    profile: str = ""
    composition: str = ""
    target_profile: str = ""
    target_composition: str = ""
    last_computed: str = ""
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

        inventory_id = self.infin_id or self.name

        if inventory_id:
            self.positions = data.get_inventory(dt, self.infin_id, self.name)
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

        def get_float(k: str) -> float:
            val = get_str(k)
            if val:
                try:
                    return float(val.replace(',', '.'))
                except ValueError:
                    pass
            return 0.0

        port = cls(
            name=get_str("Name"),
            comment=get_str("comment"),
            infin_id=get_str("InfinId"),
            insurance_contract=get_str("insuranceContract"),
            account_name=get_str("accountName"),
            client=get_str("client"),
            insurer=get_str("insurer"),
            custodian=get_str("custodian"),
            sales=get_str("sales"),
            fund_type=get_str("Type"),
            mandat_type=get_str("AccountType"),
            av_type=get_str("AVType"),
            ccy=get_str("ccy"),
            profile=get_str("profile"),
            composition=get_str("composition"),
            target_profile=get_str("targetProfile"),
            target_composition=get_str("targetComposition"),
            last_computed=get_str("lastComputed"),
            cash_and_treso=get_float("CashAndTreso"),
            aum=get_float("AUM")
        )

        creation_date_str = get_str("creationDate")
        if creation_date_str:
            try:
                port.creation_date = dateutil.parser.parse(creation_date_str)
            except Exception:
                pass

        return port
