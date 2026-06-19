from datetime import datetime
from typing import Dict, Any

class Referential:
    def __init__(self):
        self.positions_by_date_by_fund_id: Dict[str, Dict[datetime, Dict[str, Any]]] = {}
        self.instruments_infin_by_key: Dict[datetime, Dict[str, Dict[str, Any]]] = {}
        self.portfolios_by_key: Dict[datetime, Dict[str, Any]] = {}

    def get_inventory_infin(self, dt: datetime, fund: Any) -> Dict[str, Any]:
        from position_factory import PositionFactory
        from configuration import Configuration

        fund_id = fund.infin_id if fund.infin_id else fund.name

        if fund_id not in self.positions_by_date_by_fund_id:
            self.positions_by_date_by_fund_id[fund_id] = {}

        positions_by_date = self.positions_by_date_by_fund_id[fund_id]

        if dt in positions_by_date:
            return positions_by_date[dt]

        config = Configuration()

        if fund_id in config.funds_through_xml:
            positions = PositionFactory.get_positions_by_date_from_xml_file(dt, fund)
        else:
            path = config.create_inventory_csv_path(dt, fund_id)
            positions = PositionFactory.get_positions_by_date_from_infin_csv_file(path, dt, fund)

        positions_by_date[dt] = positions
        return positions

    def get_instruments_infin_by_key(self, dt: datetime, by_infin_id: bool) -> Dict[str, Any]:
        from instrument_factory import InstrumentFactory
        from configuration import Configuration

        boolean_str = str(by_infin_id)

        if dt not in self.instruments_infin_by_key:
            self.instruments_infin_by_key[dt] = {}

        instruments_by_date = self.instruments_infin_by_key[dt]

        if boolean_str in instruments_by_date:
            return instruments_by_date[boolean_str]

        config = Configuration()
        path = config.create_instruments_referential_path(dt)
        instruments = InstrumentFactory.get_instruments_from_file(path, by_infin_id)
        instruments_by_date[boolean_str] = instruments

        return instruments

    def get_portfolios_infin_by_key(self, dt: datetime) -> Dict[str, Any]:
        from portfolio_factory import PortfolioFactory
        from configuration import Configuration

        if dt in self.portfolios_by_key:
            return self.portfolios_by_key[dt]

        config = Configuration()
        path = config.create_portfolios_referential_path(dt)
        portfolios = PortfolioFactory.get_portfolios_from_file(path, dt)

        self.portfolios_by_key[dt] = portfolios
        return portfolios

    def get_configuration(self) -> Any:
        from configuration import Configuration
        return Configuration()
