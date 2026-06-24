import logging
from datetime import datetime
from typing import Dict, Any
import pandas as pd
from portfolio import Portfolio
from position import Position

logger = logging.getLogger(__name__)

MONEY_MARKET_ID = "MM_FUND_PLACEHOLDER"

def _create_dummy_portfolio(name: str) -> Portfolio:
    return Portfolio(
        fund_type="", fund_id="", symbol="", name=name, currency="",
        creation_date=datetime(1970,1,1), inception_date=datetime(1970,1,1),
        active=False, custodian="", mandate_type="", account_type="",
        life_insurer="", life_insurer_product="", profile="", model="", manager="",
        srri="", sri="", via=""
    )

def compute_benchmark(target_portfolio: Portfolio, apply_time_adjustment: bool = False) -> Portfolio:
    benchmark = _create_dummy_portfolio(name=f"Benchmark for {target_portfolio.name}")

    buckets = _load_buckets()
    defensive_model = _load_model_composition("ModelDefensive")
    aggressive_model = _load_model_composition("ModelAggressive")

    equity_delta = _get_equity_delta(target_portfolio)

    interpolated_buckets = _interpolate_models(defensive_model, aggressive_model, equity_delta)

    for bucket_name, bucket_weight in interpolated_buckets.items():
        if bucket_weight > 0:
            if bucket_port := buckets.get(bucket_name):
                for pos in bucket_port.positions.values():
                    new_pos = pos.clone()
                    new_pos.weight *= bucket_weight
                    _add_position_to_benchmark(benchmark, new_pos)
            else:
                logger.warning(f"Bucket '{bucket_name}' found in model but not defined in Buckets table.")

    if apply_time_adjustment:
        _apply_time_adjustment(benchmark, target_portfolio)

    _prune_small_positions(benchmark, target_portfolio.aum, 5000.0)
    _calculate_quantities(benchmark, target_portfolio.aum)

    return benchmark

def _apply_time_adjustment(bench: Portfolio, target_portfolio: Portfolio) -> None:
    if not target_portfolio.creation_date:
        raise ValueError(f"Creation date is missing for portfolio {target_portfolio.name}. Cannot apply time adjustment.")

    years_exist = (datetime.now() - target_portfolio.creation_date).days / 365.0
    time_factor = max(0.0, min(1.0, years_exist))

    for pos in bench.positions.values():
        pos.weight *= time_factor

    mm_weight = 1.0 - time_factor
    if mm_weight > 0:
        mm_pos = Position(pos_id=MONEY_MARKET_ID, weight=mm_weight)

        try:
            import data
            instr_dict = data.get_instruments(datetime.now(), by_infin_id=True)
            if instr_dict and MONEY_MARKET_ID in instr_dict:
                mm_pos.pos_instrument = instr_dict[MONEY_MARKET_ID]
        except Exception:
            pass

        _add_position_to_benchmark(bench, mm_pos)

def _prune_small_positions(bench: Portfolio, total_aum: float, threshold: float) -> None:
    while bench.positions:
        sorted_positions = sorted(bench.positions.values(), key=lambda p: p.weight * total_aum)
        smallest_pos = sorted_positions[0]
        amount = smallest_pos.weight * total_aum

        if amount >= threshold or amount <= 0:
            break

        del bench.positions[smallest_pos.pos_id]

        total_weight = sum(p.weight for p in bench.positions.values())
        if total_weight > 0:
            for p in bench.positions.values():
                p.weight /= total_weight

def _calculate_quantities(bench: Portfolio, total_aum: float) -> None:
    for pos in bench.positions.values():
        pos.amount_base_cur = pos.weight * total_aum
        price = pos.pos_instrument.last_close if pos.pos_instrument else pos.price

        pos.qty = (pos.amount_base_cur / price) if price else 0.0
        pos.price = price

def _get_equity_delta(port: Portfolio) -> float:
    try:
        delta = float(port.exposure_limits.get("EquityDelta", port.profile))
    except (ValueError, TypeError):
        logger.warning(f"Could not determine Equity Delta for {port.name}. Defaulting to 0.")
        delta = 0.0

    return delta / 100.0 if delta > 1.0 else delta

def _load_buckets() -> Dict[str, Portfolio]:
    import data
    config = data.get_configuration()
    buckets: Dict[str, Portfolio] = {}

    try:
        df = pd.read_csv("buckets_data.csv")

        instr_dict = {}
        try:
            instr_dict = data.get_instruments(datetime.now(), by_infin_id=True)
        except Exception:
            pass

        for _, row in df.iterrows():
            b_name = str(row.iloc[0]).strip()
            instr_id = str(row.iloc[1]).strip()

            try:
                weight = float(row.iloc[3])
            except (ValueError, TypeError):
                continue

            if not b_name:
                continue

            if b_name not in buckets:
                buckets[b_name] = _create_dummy_portfolio(name=b_name)

            pos = Position(pos_id=instr_id, weight=weight)
            if instr_dict and instr_id in instr_dict:
                pos.pos_instrument = instr_dict[instr_id]

            buckets[b_name].positions[instr_id] = pos

    except Exception as e:
        logger.error(f"Failed to load buckets from CSV: {e}")

    return buckets

def _load_model_composition(range_name: str) -> Dict[str, float]:
    composition: Dict[str, float] = {}
    try:
        file_map = {
            "ModelDefensive": "model_defensive.csv",
            "ModelAggressive": "model_aggressive.csv"
        }

        if range_name in file_map:
            df = pd.read_csv(file_map[range_name])
            for _, row in df.iterrows():
                b_name = str(row.iloc[0]).strip()
                try:
                    weight = float(row.iloc[1])
                    if b_name:
                        composition[b_name] = composition.get(b_name, 0.0) + weight
                except (ValueError, TypeError):
                    continue

    except Exception as e:
        logger.error(f"Failed to load model {range_name}: {e}")

    return composition

def _interpolate_models(defensive: Dict[str, float], aggressive: Dict[str, float], delta: float) -> Dict[str, float]:
    all_buckets = set(defensive.keys()) | set(aggressive.keys())
    result = {}

    for bucket in all_buckets:
        w_def = defensive.get(bucket, 0.0)
        w_agg = aggressive.get(bucket, 0.0)
        w_final = w_def + (w_agg - w_def) * delta

        if w_final != 0.0:
            result[bucket] = w_final

    return result

def _add_position_to_benchmark(bench: Portfolio, new_pos: Position) -> None:
    if new_pos.pos_id in bench.positions:
        bench.positions[new_pos.pos_id].weight += new_pos.weight
    else:
        bench.positions[new_pos.pos_id] = new_pos
