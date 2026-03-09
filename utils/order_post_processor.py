from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pandas as pd

from sales_data import SalesAnalyzer
from ui.shared.sku_utils import CHILDREN_PREFIXES
from utils.logging_config import get_logger
from utils.material_constraints import MaterialConstraint

if TYPE_CHECKING:
    from utils.pattern_optimizer import PatternSet

logger = get_logger(__name__)


@dataclass
class ConstraintFlags:
    enforce_min: bool = False
    enforce_max: bool = False
    enforce_parity: bool = False
    cap_by_sales: bool = False
    drop_excess: bool = False
    match_children: bool = False


@dataclass
class ConstraintFeedback:
    capped_colors: dict[str, tuple[int, int]]
    dropped_colors: list[str]
    redistributed_colors: dict[str, int]

    @staticmethod
    def empty() -> ConstraintFeedback:
        return ConstraintFeedback(
            capped_colors={},
            dropped_colors=[],
            redistributed_colors={},
        )


def apply_order_constraints(
        pattern_results: dict,
        model: str,
        colors: list[str],
        pattern_set: PatternSet,
        monthly_agg: pd.DataFrame | None,
        priority_skus: pd.DataFrame,
        constraint: MaterialConstraint | None,
        flags: ConstraintFlags,
        size_aliases: dict[str, str],
        min_per_pattern: int,
        algorithm_mode: str,
) -> tuple[dict, ConstraintFeedback]:
    feedback = ConstraintFeedback.empty()

    if flags.cap_by_sales or flags.drop_excess:
        pattern_results, feedback = apply_color_cap(
            pattern_results, model, colors, monthly_agg, priority_skus,
            pattern_set, size_aliases, min_per_pattern, algorithm_mode,
            flags.drop_excess,
        )

    if constraint and (flags.enforce_min or flags.enforce_max):
        pattern_results = apply_material_min_max(
            pattern_results, constraint, pattern_set, colors,
            flags.enforce_min, flags.enforce_max,
        )

    if constraint and flags.enforce_parity and constraint.even_only:
        pattern_results = apply_parity(pattern_results, pattern_set, colors)

    if flags.match_children and _is_children_model(model):
        pattern_results = apply_children_distribution(
            pattern_results, model, colors, pattern_set,
            monthly_agg, priority_skus, size_aliases, min_per_pattern, algorithm_mode,
        )

    return pattern_results, feedback


def _is_children_model(model: str) -> bool:
    return model[:2].lower() in CHILDREN_PREFIXES


def _get_total_produced_for_color(result: dict) -> int:
    return sum(result.get("produced", {}).values())


def _get_total_pieces_per_pattern(pattern_set: PatternSet) -> dict[int, int]:
    return {p.id: sum(p.sizes.values()) for p in pattern_set.patterns}


def apply_color_cap(
        pattern_results: dict,
        model: str,
        colors: list[str],
        monthly_agg: pd.DataFrame | None,
        priority_skus: pd.DataFrame,
        pattern_set: PatternSet,
        size_aliases: dict[str, str],
        min_per_pattern: int,
        algorithm_mode: str,
        drop_excess: bool,
) -> tuple[dict, ConstraintFeedback]:
    feedback = ConstraintFeedback.empty()
    reopt_args = (pattern_set, priority_skus, monthly_agg, size_aliases, min_per_pattern, algorithm_mode)

    sales_12m = _get_12m_sales_by_color(monthly_agg, model, colors)
    stock_by_color = _get_stock_by_color(priority_skus, model, colors)
    max_proposed = {c: max(0, sales_12m.get(c, 0) - stock_by_color.get(c, 0)) for c in colors}

    over_cap, under_cap = _classify_colors_by_cap(pattern_results, colors, max_proposed)

    total_excess_qty = _reduce_over_cap_colors(
        pattern_results, feedback, over_cap, max_proposed, model, reopt_args,
    )

    if total_excess_qty > 0 and under_cap:
        _redistribute_excess(
            pattern_results, feedback, under_cap, max_proposed,
            sales_12m, total_excess_qty, model, reopt_args,
        )

    if drop_excess:
        _drop_zero_cap_colors(pattern_results, feedback, max_proposed)

    return pattern_results, feedback


def _classify_colors_by_cap(
    pattern_results: dict, colors: list[str], max_proposed: dict[str, int],
) -> tuple[list[str], list[str]]:
    over_cap: list[str] = []
    under_cap: list[str] = []
    for color in colors:
        if color not in pattern_results:
            continue
        produced = _get_total_produced_for_color(pattern_results[color])
        cap = max_proposed[color]
        if produced > cap > 0:
            over_cap.append(color)
        elif produced <= cap:
            under_cap.append(color)
    return over_cap, under_cap


def _reduce_over_cap_colors(
    pattern_results: dict, feedback: ConstraintFeedback,
    over_cap_colors: list[str], max_proposed: dict[str, int],
    model: str, reopt_args: tuple,
) -> int:
    total_excess_qty = 0
    for color in over_cap_colors:
        original = _get_total_produced_for_color(pattern_results[color])
        pattern_results[color] = _reoptimize_color_to_target(
            model, color, max_proposed[color], *reopt_args,
        )
        new_produced = _get_total_produced_for_color(pattern_results[color])
        total_excess_qty += original - new_produced
        feedback.capped_colors[color] = (original, new_produced)
    return total_excess_qty


def _redistribute_excess(
    pattern_results: dict, feedback: ConstraintFeedback,
    under_cap_colors: list[str], max_proposed: dict[str, int],
    sales_12m: dict[str, int], total_excess_qty: int,
    model: str, reopt_args: tuple,
) -> None:
    headroom = {
        c: max(0, max_proposed[c] - _get_total_produced_for_color(pattern_results[c]))
        for c in under_cap_colors
    }
    total_headroom = sum(headroom.values())
    if total_headroom <= 0:
        return

    sorted_colors = sorted(under_cap_colors, key=lambda c: sales_12m.get(c, 0), reverse=True)
    remaining = total_excess_qty

    for color in sorted_colors:
        if remaining <= 0 or headroom.get(color, 0) <= 0:
            continue
        share = min(
            headroom[color],
            int(math.ceil(total_excess_qty * headroom[color] / total_headroom)),
            remaining,
        )
        if share <= 0:
            continue

        produced = _get_total_produced_for_color(pattern_results[color])
        pattern_results[color] = _reoptimize_color_to_target(
            model, color, produced + share, *reopt_args,
        )
        added = _get_total_produced_for_color(pattern_results[color]) - produced
        if added > 0:
            feedback.redistributed_colors[color] = added
            remaining -= added


def _drop_zero_cap_colors(
    pattern_results: dict, feedback: ConstraintFeedback, max_proposed: dict[str, int],
) -> None:
    to_drop = [c for c in pattern_results if max_proposed.get(c, 0) == 0]
    for color in to_drop:
        feedback.dropped_colors.append(color)
        del pattern_results[color]


def _reoptimize_color_to_target(
        model: str,
        color: str,
        target_qty: int,
        pattern_set: PatternSet,
        priority_skus: pd.DataFrame,
        monthly_agg: pd.DataFrame | None,
        size_aliases: dict[str, str],
        min_per_pattern: int,
        algorithm_mode: str,
) -> dict:
    original_sizes = _get_size_quantities_for_color(priority_skus, model, color, size_aliases)
    if not original_sizes:
        return _empty_result()

    original_total = sum(original_sizes.values())
    if original_total == 0:
        return _empty_result()

    scale = target_qty / original_total if original_total > 0 else 0
    scaled_sizes = {
        size: max(1, int(round(qty * scale)))
        for size, qty in original_sizes.items()
        if qty > 0
    }

    if not scaled_sizes:
        return _empty_result()

    size_sales_history = None
    if monthly_agg is not None and not monthly_agg.empty:
        size_sales_history = SalesAnalyzer.calculate_size_sales_history(
            monthly_agg, model, color, size_aliases, months=2
        )

    return SalesAnalyzer.optimize_pattern_with_aliases(
        priority_skus, model, color, pattern_set, size_aliases,
        min_per_pattern, algorithm_mode,
        size_sales_history, scaled_sizes, min_sales_threshold=2,
    )


def _get_size_quantities_for_color(
        priority_skus: pd.DataFrame,
        model: str,
        color: str,
        size_aliases: dict[str, str],
) -> dict[str, int]:
    model_color = pd.DataFrame(
        priority_skus[(priority_skus["MODEL"] == model) & (priority_skus["COLOR"] == color)]
    )
    if model_color.empty:
        return {}

    result: dict[str, int] = {}
    for _, row in model_color.iterrows():
        size_code = str(row["SIZE"])
        stock = int(row.get("STOCK", 0) or 0)
        period_sales = int(row.get("PERIOD_SALES", 0) or 0)
        order_qty = max(0, period_sales - stock)
        if order_qty > 0:
            alias = size_aliases.get(size_code, size_code)
            result[alias] = result.get(alias, 0) + order_qty
    return result


def apply_material_min_max(
        pattern_results: dict,
        constraint: MaterialConstraint,
        pattern_set: PatternSet,
        colors: list[str],
        enforce_min: bool,
        enforce_max: bool,
) -> dict:
    pieces_per_pattern = _get_total_pieces_per_pattern(pattern_set)

    for pattern in pattern_set.patterns:
        pid = pattern.id
        ppp = pieces_per_pattern.get(pid, 0)
        if ppp == 0:
            continue

        total_uses = sum(
            pattern_results.get(color, {}).get("allocation", {}).get(pid, 0)
            for color in colors
            if color in pattern_results
        )
        total_pieces = ppp * total_uses

        if enforce_min and constraint.min_qty and 0 < total_pieces < constraint.min_qty:
            needed_uses = math.ceil(constraint.min_qty / ppp)
            _scale_pattern_allocations(pattern_results, colors, pid, total_uses, needed_uses)

        if enforce_max and constraint.max_qty and total_pieces > constraint.max_qty:
            allowed_uses = constraint.max_qty // ppp
            _scale_pattern_allocations(pattern_results, colors, pid, total_uses, allowed_uses)

    _recompute_produced_excess(pattern_results, pattern_set)
    return pattern_results


def _scale_pattern_allocations(
        pattern_results: dict,
        colors: list[str],
        pattern_id: int,
        current_total: int,
        target_total: int,
) -> None:
    if current_total == 0:
        return

    scale = target_total / current_total
    remainder = target_total

    active_colors = [
        c for c in colors
        if c in pattern_results and pattern_results[c].get("allocation", {}).get(pattern_id, 0) > 0
    ]

    for i, color in enumerate(active_colors):
        alloc = pattern_results[color]["allocation"]
        current = alloc.get(pattern_id, 0)
        if i == len(active_colors) - 1:
            new_val = max(0, remainder)
        else:
            new_val = max(0, int(round(current * scale)))
            remainder -= new_val
        alloc[pattern_id] = new_val


def _recompute_produced_excess(pattern_results: dict, pattern_set: PatternSet) -> None:
    pattern_map = {p.id: p for p in pattern_set.patterns}

    for color, result in pattern_results.items():
        allocation = result.get("allocation", {})
        produced: dict[str, int] = {}
        for pid, count in allocation.items():
            pattern = pattern_map.get(pid)
            if pattern is None:
                continue
            for size, qty in pattern.sizes.items():
                produced[size] = produced.get(size, 0) + qty * count

        result["produced"] = produced
        result["total_patterns"] = sum(allocation.values())

        original_excess = result.get("excess", {})
        new_excess: dict[str, int] = {}
        for size, prod_qty in produced.items():
            original_exc = original_excess.get(size, 0)
            original_prod = result.get("_original_produced", {}).get(size, prod_qty)
            if original_prod > 0:
                new_excess[size] = max(0, int(round(original_exc * prod_qty / original_prod)))
            else:
                new_excess[size] = 0
        result["excess"] = new_excess
        result["total_excess"] = sum(new_excess.values())


def apply_parity(pattern_results: dict, pattern_set: PatternSet, colors: list[str]) -> dict:
    for color in colors:
        if color not in pattern_results:
            continue
        allocation = pattern_results[color].get("allocation", {})
        for pid in allocation:
            count = allocation[pid]
            if count % 2 != 0:
                allocation[pid] = count + 1

    _recompute_produced_excess(pattern_results, pattern_set)
    return pattern_results


def apply_children_distribution(
        pattern_results: dict,
        model: str,
        colors: list[str],
        pattern_set: PatternSet,
        monthly_agg: pd.DataFrame | None,
        priority_skus: pd.DataFrame,
        size_aliases: dict[str, str],
        min_per_pattern: int,
        algorithm_mode: str,
) -> dict:
    if monthly_agg is None or monthly_agg.empty:
        return pattern_results

    total_order = sum(
        _get_total_produced_for_color(pattern_results.get(c, {}))
        for c in colors if c in pattern_results
    )
    if total_order == 0:
        return pattern_results

    color_sales = _get_color_distribution_4m(monthly_agg, model, colors)
    total_color_sales = sum(color_sales.values())
    if total_color_sales == 0:
        return pattern_results

    for color in colors:
        if color not in pattern_results:
            continue
        result = _redistribute_color_by_sales(
            model, color, total_order, color_sales, total_color_sales,
            monthly_agg, priority_skus, pattern_set, size_aliases, min_per_pattern, algorithm_mode,
        )
        if result is not None:
            pattern_results[color] = result

    return pattern_results


def _redistribute_color_by_sales(
    model: str, color: str, total_order: int,
    color_sales: dict[str, int], total_color_sales: int,
    monthly_agg: pd.DataFrame, priority_skus: pd.DataFrame,
    pattern_set: PatternSet, size_aliases: dict[str, str],
    min_per_pattern: int, algorithm_mode: str,
) -> dict | None:
    color_target = max(0, int(round(total_order * color_sales.get(color, 0) / total_color_sales)))
    if color_target == 0:
        return None

    size_sales = SalesAnalyzer.calculate_size_sales_history(monthly_agg, model, color, size_aliases, months=4)
    total_size_sales = sum(size_sales.values())
    if total_size_sales == 0:
        return None

    size_quantities = {
        size: max(1, int(round(color_target * sales / total_size_sales)))
        for size, sales in size_sales.items()
    }
    if not size_quantities:
        return None

    size_sales_history = SalesAnalyzer.calculate_size_sales_history(monthly_agg, model, color, size_aliases, months=2)

    return SalesAnalyzer.optimize_pattern_with_aliases(
        priority_skus, model, color, pattern_set, size_aliases,
        min_per_pattern, algorithm_mode,
        size_sales_history, size_quantities, min_sales_threshold=2,
    )


def _get_12m_sales_by_color(
        monthly_agg: pd.DataFrame | None,
        model: str,
        colors: list[str],
) -> dict[str, int]:
    if monthly_agg is None or monthly_agg.empty:
        return {}

    sales_df = SalesAnalyzer.get_last_n_months_sales_by_color(monthly_agg, model, colors, months=12)
    if sales_df.empty:
        return {}

    result: dict[str, int] = {}
    for _, row in sales_df.iterrows():
        color = str(row.get("color", ""))
        numeric_cols = [c for c in sales_df.columns if c != "color"]
        total = sum(int(row.get(c, 0) or 0) for c in numeric_cols)
        result[color] = total
    return result


def _get_stock_by_color(
        priority_skus: pd.DataFrame,
        model: str,
        colors: list[str],
) -> dict[str, int]:
    model_df = pd.DataFrame(priority_skus[priority_skus["MODEL"] == model])
    if model_df.empty:
        return {}

    result: dict[str, int] = {}
    for color in colors:
        color_df = model_df[model_df["COLOR"] == color]
        result[color] = int(color_df["STOCK"].sum()) if not color_df.empty else 0
    return result


def _get_color_distribution_4m(
        monthly_agg: pd.DataFrame,
        model: str,
        colors: list[str],
) -> dict[str, int]:
    sales_df = SalesAnalyzer.get_last_n_months_sales_by_color(monthly_agg, model, colors, months=4)
    if sales_df.empty:
        return {}

    result: dict[str, int] = {}
    for _, row in sales_df.iterrows():
        color = str(row.get("color", ""))
        numeric_cols = [c for c in sales_df.columns if c != "color"]
        total = sum(int(row.get(c, 0) or 0) for c in numeric_cols)
        result[color] = total
    return result


def _empty_result() -> dict:
    return {
        "allocation": {},
        "produced": {},
        "excess": {},
        "total_patterns": 0,
        "total_excess": 0,
        "all_covered": False,
    }
