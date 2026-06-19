import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List
from portfolio import Portfolio
from position import Position

logger = logging.getLogger(__name__)

MONEY_MARKET_ID = "MM_FUND_PLACEHOLDER"

class BenchmarkFactory:
    @staticmethod
    def compute_benchmark(target_portfolio: Portfolio, apply_time_adjustment: bool = False) -> Portfolio:
        benchmark = Portfolio()
        benchmark.name = f"Benchmark for {target_portfolio.name}"

        # 1. Load Data
        buckets = BenchmarkFactory._load_buckets()
        defensive_model = BenchmarkFactory._load_model_composition("ModelDefensive")
        aggressive_model = BenchmarkFactory._load_model_composition("ModelAggressive")

        # 2. Determine Interpolation Factor (Equity Delta)
        equity_delta = BenchmarkFactory._get_equity_delta(target_portfolio)

        # 3. Interpolate Bucket Weights
        interpolated_buckets = BenchmarkFactory._interpolate_models(defensive_model, aggressive_model, equity_delta)

        # 4. Construct Benchmark Portfolio (Initial Pass)
        for bucket_name, bucket_weight in interpolated_buckets.items():
            if bucket_weight > 0:
                if bucket_name in buckets:
                    bucket_port = buckets[bucket_name]
                    for pos in bucket_port.positions.values():
                        new_pos = pos.clone()
                        new_pos.weight = new_pos.weight * bucket_weight
                        BenchmarkFactory._add_position_to_benchmark(benchmark, new_pos)
                else:
                    logger.warning(f"Bucket '{bucket_name}' found in model but not defined in Buckets table.")

        # 5. Apply Time Adjustment (Optional)
        if apply_time_adjustment:
            BenchmarkFactory._apply_time_adjustment(benchmark, target_portfolio)

        # 6. Apply Minimum Quantity Threshold (Iterative Pruning)
        BenchmarkFactory._prune_small_positions(benchmark, target_portfolio.aum, 5000.0)

        # 7. Final Quantity Calculation
        BenchmarkFactory._calculate_quantities(benchmark, target_portfolio.aum)

        return benchmark

    @staticmethod
    def _apply_time_adjustment(bench: Portfolio, target_portfolio: Portfolio) -> None:
        creation_date = target_portfolio.creation_date

        if not creation_date:
            raise ValueError(f"Creation date is missing for portfolio {target_portfolio.name}. Cannot apply time adjustment.")

        years_exist = (datetime.now() - creation_date).days / 365.0

        if years_exist >= 1:
            time_factor = 1.0
        elif years_exist < 0:
            time_factor = 0.0
        else:
            time_factor = years_exist

        for pos in bench.positions.values():
            pos.weight = pos.weight * time_factor

        mm_weight = 1.0 - time_factor

        if mm_weight > 0:
            mm_pos = Position()
            mm_pos.pos_id = MONEY_MARKET_ID
            mm_pos.weight = mm_weight

            import data
            try:
                instr_dict = data.get_instruments(datetime.now(), by_infin_id=True)
                if instr_dict and MONEY_MARKET_ID in instr_dict:
                    mm_pos.pos_instrument = instr_dict[MONEY_MARKET_ID]
            except Exception:
                pass

            BenchmarkFactory._add_position_to_benchmark(bench, mm_pos)

    @staticmethod
    def _prune_small_positions(bench: Portfolio, total_aum: float, threshold: float) -> None:
        continue_pruning = True

        while continue_pruning and len(bench.positions) > 0:
            continue_pruning = False

            # Sort positions by amount asc
            sorted_positions = sorted(bench.positions.values(), key=lambda p: p.weight * total_aum)

            if sorted_positions:
                smallest_pos = sorted_positions[0]
                amount = smallest_pos.weight * total_aum

                if 0 < amount < threshold:
                    del bench.positions[smallest_pos.pos_id]

                    total_weight = sum(p.weight for p in bench.positions.values())

                    if total_weight > 0:
                        for p in bench.positions.values():
                            p.weight = p.weight / total_weight

                    continue_pruning = True

    @staticmethod
    def _calculate_quantities(bench: Portfolio, total_aum: float) -> None:
        for pos in bench.positions.values():
            pos.amount_base_cur = pos.weight * total_aum

            price = 0.0
            if pos.pos_instrument is not None:
                price = pos.pos_instrument.last_close

            if price == 0.0:
                price = pos.price

            if price != 0.0:
                pos.qty = pos.amount_base_cur / price
            else:
                pos.qty = 0.0

            pos.price = price

    @staticmethod
    def _get_equity_delta(port: Portfolio) -> float:
        delta = 0.0
        found = False

        if port.exposure_limits and "EquityDelta" in port.exposure_limits:
            try:
                delta = float(port.exposure_limits["EquityDelta"])
                found = True
            except ValueError:
                pass

        if not found:
            try:
                delta = float(port.profile)
                found = True
            except ValueError:
                pass

        if not found:
            logger.warning(f"Could not determine Equity Delta for {port.name}. Defaulting to 0.")
            delta = 0.0

        if delta > 1.0:
            delta = delta / 100.0

        return delta

    @staticmethod
    def _load_buckets() -> Dict[str, Portfolio]:
        # Implementation assumes usage of pandas to read 'BucketsData' range if needed
        # Due to lack of access to running Excel app, this acts as a stub or reads from a config file.
        # It could be adapted to read from a specific csv/xlsx instead of named range
        logger.warning("_load_buckets reading from excel named range is omitted, returning empty dict.")
        return {}

    @staticmethod
    def _load_model_composition(range_name: str) -> Dict[str, float]:
        logger.warning(f"_load_model_composition reading from excel named range {range_name} is omitted, returning empty dict.")
        return {}

    @staticmethod
    def _interpolate_models(defensive: Dict[str, float], aggressive: Dict[str, float], delta: float) -> Dict[str, float]:
        result = {}
        all_buckets = set(defensive.keys()).union(set(aggressive.keys()))

        for bucket in all_buckets:
            w_def = defensive.get(bucket, 0.0)
            w_agg = aggressive.get(bucket, 0.0)

            w_final = w_def + (w_agg - w_def) * delta

            if w_final != 0.0:
                result[bucket] = w_final

        return result

    @staticmethod
    def _add_position_to_benchmark(bench: Portfolio, new_pos: Position) -> None:
        if new_pos.pos_id in bench.positions:
            bench.positions[new_pos.pos_id].weight += new_pos.weight
        else:
            bench.positions[new_pos.pos_id] = new_pos
