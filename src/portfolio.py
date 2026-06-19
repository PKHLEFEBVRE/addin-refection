from datetime import datetime
from typing import Dict, Any, Optional
from position import Position

class Portfolio:
    def __init__(self):
        self.name: str = ""
        self.comment: str = ""
        self.infin_id: str = ""
        self.insurance_contract: str = ""
        self.account_name: str = ""
        self.client: str = ""
        self.creation_date: Optional[datetime] = None
        self.insurer: str = ""
        self.custodian: str = ""
        self.sales: str = ""
        self.mandat_type: str = ""
        self.fund_type: str = ""
        self.av_type: str = ""
        self.ccy: str = ""
        self.profile: str = ""
        self.composition: str = ""
        self.target_profile: str = ""
        self.target_composition: str = ""
        self.last_computed: str = ""
        self.cash_and_treso: float = 0.0
        self.aum: float = 0.0
        self.exposure_limits: Dict[str, Any] = {}
        self.positions: Dict[str, Position] = {}
        self.trades: Dict[str, Position] = {}

        self._equity_delta: float = 0.0
        self._equity_delta_computed: bool = False

    def set_trades(self, trades_dict: Dict[str, Position]) -> None:
        if trades_dict is not None:
            self.trades = trades_dict

    def get_positions_with_trades(self) -> Dict[str, Position]:
        sim_positions: Dict[str, Position] = {}

        # 1. Clone original positions
        for key, pos in self.positions.items():
            sim_positions[key] = pos.clone()

        # 2. Calculate trade cost (excluding Cash "10")
        total_trade_cost = 0.0
        for key, trade in self.trades.items():
            if trade.pos_id != "10":
                total_trade_cost += trade.amount_base_cur

        # 3. Apply trades
        for key, trade in self.trades.items():
            if trade.pos_id in sim_positions:
                new_pos = sim_positions[trade.pos_id]
                new_pos.qty += trade.qty
                new_pos.amount_base_cur += trade.amount_base_cur
            else:
                sim_positions[trade.pos_id] = trade.clone()

        # 4. Automatic Financing (Subtract cost from Cash "10")
        if "10" in sim_positions:
            sim_positions["10"].amount_base_cur -= total_trade_cost
        else:
            print(f"Warning: Cash position '10' not found in portfolio {self.name}")

        # 5. Recompute Weights
        sim_aum = sum(pos.amount_base_cur for pos in sim_positions.values())

        if sim_aum != 0:
            for pos in sim_positions.values():
                pos.weight = pos.amount_base_cur / sim_aum

        return sim_positions

    def get_computed_equity_delta(self) -> float:
        if self._equity_delta_computed:
            return self._equity_delta

        sum_delta = 0.0

        if self.positions:
            for current_pos in self.positions.values():
                if current_pos.pos_instrument is not None:
                    sum_delta += current_pos.weight * current_pos.pos_instrument.equity_delta

        self._equity_delta = sum_delta
        self._equity_delta_computed = True

        return self._equity_delta

    def get_positions(self, dt: datetime) -> Dict[str, Position]:
        # To avoid circular imports, Data is imported lazily
        import data

        # If positions are already loaded, return them
        if self.positions:
            return self.positions

        # Otherwise, load them
        inventory_id = self.infin_id
        if not inventory_id:
            inventory_id = self.name

        if inventory_id:
            self.positions = data.get_inventory(dt, self)

            # Compute AUM and Weights
            total_amount = sum(pos.amount_base_cur for pos in self.positions.values())
            self.aum = total_amount

            if self.aum != 0:
                for pos in self.positions.values():
                    pos.weight = pos.amount_base_cur / self.aum

        # Reset computed values when positions change
        self._equity_delta_computed = False

        return self.positions
