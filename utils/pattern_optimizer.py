from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass

from utils.settings_manager import load_settings

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    id: int
    name: str
    sizes: dict[str, int]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Pattern":
        return cls(**data)


@dataclass
class PatternSet:
    id: int
    name: str
    size_names: list[str]
    patterns: list[Pattern]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "size_names": self.size_names,
            "patterns": [p.to_dict() for p in self.patterns],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PatternSet":
        return cls(
            id=data["id"],
            name=data["name"],
            size_names=data.get("size_names", ["XL", "L", "M", "S", "XS"]),
            patterns=[Pattern.from_dict(p) for p in data["patterns"]],
        )


PATTERN_SETS_FILE = "./saved_pattern_sets.json"
OPTIMIZER_PATTERN_SETS_FILE = "./utils/optimizer_pattern_sets.json"


def get_min_order_per_pattern() -> int:
    settings = load_settings()
    return settings.get("optimizer", {}).get("min_order_per_pattern", 5)  # type: ignore[no-any-return]


def load_pattern_sets(file_path: str | None = None) -> list[PatternSet]:
    if file_path is None:
        file_path = PATTERN_SETS_FILE

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [PatternSet.from_dict(ps) for ps in data]
        except (KeyError, ValueError):
            pass
    return [
        PatternSet(
            id=1,
            name="Default Set",
            size_names=["XL", "L", "M", "S", "XS"],
            patterns=[
                Pattern(1, "L + XL", {"L": 1, "XL": 1}),
                Pattern(2, "S + M", {"S": 1, "M": 1}),
                Pattern(3, "M + M", {"M": 2}),
                Pattern(4, "S + L", {"S": 1, "L": 1}),
                Pattern(5, "XS + XL", {"XS": 1, "XL": 1}),
                Pattern(6, "M + L", {"M": 1, "L": 1}),
            ],
        )
    ]


def save_pattern_sets(pattern_sets: list[PatternSet], file_path: str | None = None) -> None:
    if file_path is None:
        file_path = PATTERN_SETS_FILE

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump([ps.to_dict() for ps in pattern_sets], f, indent=2)


MIN_SALES_THRESHOLD = 3


def filter_low_sales_sizes(
    quantities: dict[str, int],
    size_sales_history: dict[str, int] | None,
) -> tuple[dict[str, int], list[str]]:
    if size_sales_history is None:
        return quantities, []

    excluded_sizes = []
    filtered_quantities = {}

    for size, qty in quantities.items():
        sales = size_sales_history.get(size, 0)
        if sales < MIN_SALES_THRESHOLD:
            excluded_sizes.append(size)
        else:
            filtered_quantities[size] = qty

    return filtered_quantities, excluded_sizes


def calculate_size_priorities(size_sales_history: dict[str, int] | None) -> dict[str, float] | None:
    if size_sales_history is None or not size_sales_history:
        return None

    total_sales = sum(size_sales_history.values())
    if total_sales == 0:
        return None

    priorities = {size: sales / total_sales for size, sales in size_sales_history.items()}
    return priorities


def _get_empty_result(quantities: dict[str, int]) -> dict:
    return {
        "allocation": {},
        "produced": dict.fromkeys(quantities, 0),
        "excess": dict.fromkeys(quantities, 0),
        "total_patterns": 0,
        "total_excess": 0,
        "all_covered": False,
        "min_order_violations": [],
    }


def _find_best_solution(
    quantities: dict[str, int],
    patterns: list[Pattern],
    min_per_pattern: int,
    size_priorities: dict[str, float] | None = None,
) -> dict[int, int] | None:
    best_solution = None
    best_excess = float("inf")
    max_total = sum(quantities.values()) * 2
    min_patterns = max(quantities.values()) // 2

    for total_patterns in range(min_patterns, min(max_total + 1, min_patterns + 100)):
        solution = find_allocation_for_total(
            quantities, patterns, total_patterns, min_per_pattern, size_priorities
        )

        if solution:
            total_excess_calculated = calculate_total_excess(quantities, solution, patterns)

            if total_excess_calculated < best_excess:
                best_excess = total_excess_calculated
                best_solution = solution

                if total_excess_calculated == 0:
                    break

        if best_solution and total_patterns > min_patterns + 50:
            break

    return best_solution


def _calculate_production(
    allocation: dict[int, int], patterns: list[Pattern], quantities: dict[str, int]
) -> dict[str, int]:
    produced = dict.fromkeys(quantities, 0)
    for pattern in patterns:
        count = allocation.get(pattern.id, 0)
        if count > 0:
            for size, size_count in pattern.sizes.items():
                old_produced = produced.get(size, 0)
                produced[size] = old_produced + (count * size_count)
    return produced


def _find_violations(
    allocation: dict[int, int], patterns: list[Pattern], min_per_pattern: int
) -> list[tuple]:
    violations = []
    for pattern in patterns:
        count = allocation.get(pattern.id, 0)
        if 0 < count < min_per_pattern:
            logger.warning("Min order violation: pattern '%s' has count=%d < min=%d",
                          pattern.name, count, min_per_pattern)
            violations.append((pattern.name, count))
    return violations


def optimize_patterns(
    quantities: dict[str, int],
    patterns: list[Pattern],
    min_per_pattern: int = get_min_order_per_pattern(),
    algorithm_mode: str = "greedy_overshoot",
    size_priorities: dict[str, float] | None = None,
    size_sales_history: dict[str, int] | None = None,
) -> dict:
    logger.info("Optimizing patterns: %d sizes, %d patterns, min_order=%d", len(quantities), len(patterns), min_per_pattern)

    if not patterns or not any(quantities.values()):
        logger.warning("Early exit: no patterns (%d) or all quantities are zero", len(patterns))
        return _get_empty_result(quantities)

    filtered_quantities, excluded_sizes = filter_low_sales_sizes(quantities, size_sales_history)

    if not any(filtered_quantities.values()):
        logger.warning("All quantities filtered out, returning empty result")
        result = _get_empty_result(quantities)
        result["excluded_sizes"] = excluded_sizes
        return result

    if size_priorities is None and size_sales_history is not None:
        size_priorities = calculate_size_priorities(size_sales_history)

    best_solution = _find_best_solution(filtered_quantities, patterns, min_per_pattern, size_priorities)

    if not best_solution:
        logger.warning("No solution found via search, falling back to greedy algorithm: %s", algorithm_mode)
        if algorithm_mode == "greedy_classic":
            best_solution = greedy_classic(filtered_quantities, patterns, min_per_pattern, size_priorities)
        else:
            best_solution = greedy_overshoot(filtered_quantities, patterns, min_per_pattern, size_priorities)

    produced = _calculate_production(best_solution, patterns, filtered_quantities)
    excess = {size: produced[size] - filtered_quantities[size] for size in filtered_quantities}
    min_violations = _find_violations(best_solution, patterns, min_per_pattern)

    for size in excluded_sizes:
        produced[size] = 0
        excess[size] = 0

    result = {
        "allocation": best_solution,
        "produced": produced,
        "excess": excess,
        "total_patterns": sum(best_solution.values()),
        "total_excess": sum(excess.values()),
        "all_covered": all(produced.get(size, 0) >= filtered_quantities.get(size, 0) for size in filtered_quantities),
        "min_order_violations": min_violations,
        "algorithm_used": algorithm_mode,
        "excluded_sizes": excluded_sizes,
    }

    logger.info("Optimization result: total_patterns=%d, total_excess=%d, all_covered=%s", result["total_patterns"], result["total_excess"], result["all_covered"])

    return result


def _calculate_pattern_score(
    pattern: Pattern, remaining: dict[str, int], size_priorities: dict[str, float] | None = None
) -> int:
    score = 0

    for size, count in pattern.sizes.items():
        if remaining.get(size, 0) > 0:
            base_score = min(count, remaining[size]) * 10
            if size_priorities and size in size_priorities:
                priority_bonus = size_priorities[size] * count * 5
                size_score = base_score + priority_bonus
            else:
                size_score = base_score
            score += size_score
        else:
            penalty = count
            score -= penalty

    return score


def _calculate_greedy_score(
    pattern: Pattern, remaining: dict[str, int], size_priorities: dict[str, float] | None = None
) -> float:
    score = 0.0

    for size, count in pattern.sizes.items():
        if remaining.get(size, 0) > 0:
            base_score = min(count, remaining[size]) * 100 + remaining[size] * 10
            if size_priorities and size in size_priorities:
                priority_bonus = size_priorities[size] * count * 50
                size_score = base_score + priority_bonus
            else:
                size_score = base_score
            score += size_score
        else:
            penalty = count * 1
            score -= penalty

    return score


def _find_best_pattern_by_score(
    patterns: list[Pattern],
    remaining: dict[str, int],
    score_func,
    size_priorities: dict[str, float] | None = None,
) -> Pattern | None:
    best_pattern = None
    best_score = -float("inf")

    for pattern in patterns:
        score = score_func(pattern, remaining, size_priorities)
        if score > best_score:
            best_score = score
            best_pattern = pattern

    if not best_pattern:
        logger.warning("No best pattern found!")

    return best_pattern


def _can_allocate_pattern(
    pattern: Pattern,
    allocation: dict[int, int],
    patterns_used: int,
    total: int,
    min_per_pattern: int,
) -> bool:
    if patterns_used + min_per_pattern > total:
        return allocation[pattern.id] > 0
    return True


def _update_remaining(remaining: dict[str, int], pattern: Pattern, quantity: int) -> None:
    for size, count in pattern.sizes.items():
        old_val = remaining.get(size, 0)
        remaining[size] = old_val - (count * quantity)


def find_allocation_for_total(
    quantities: dict[str, int],
    patterns: list[Pattern],
    total: int,
    min_per_pattern: int,
    size_priorities: dict[str, float] | None = None,
) -> dict[int, int] | None:
    allocation = dict.fromkeys((p.id for p in patterns), 0)
    remaining = quantities.copy()
    patterns_used = 0

    while patterns_used < total:
        valid_patterns = [
            p
            for p in patterns
            if _can_allocate_pattern(p, allocation, patterns_used, total, min_per_pattern)
        ]

        if not valid_patterns:
            break

        best_pattern = _find_best_pattern_by_score(
            valid_patterns, remaining, _calculate_pattern_score, size_priorities
        )
        if not best_pattern:
            break

        to_allocate = min(min_per_pattern, total - patterns_used)
        if allocation[best_pattern.id] > 0:
            to_allocate = 1

        allocation[best_pattern.id] += to_allocate
        patterns_used += to_allocate

        _update_remaining(remaining, best_pattern, to_allocate)

    all_covered = all(remaining.get(size, 0) <= 0 for size in quantities)

    if all_covered:
        return allocation

    return None


def _has_remaining_demand(remaining: dict[str, int]) -> bool:
    return any(remaining[size] > 0 for size in remaining)


def _determine_allocation_quantity(
    allocation: dict[int, int], pattern_id: int, min_per_pattern: int
) -> int:
    if allocation[pattern_id] == 0:
        return min_per_pattern
    return 1


def greedy_classic(
    quantities: dict[str, int],
    patterns: list[Pattern],
    min_per_pattern: int,
    size_priorities: dict[str, float] | None = None,
) -> dict[int, int]:
    allocation = dict.fromkeys((p.id for p in patterns), 0)
    remaining = quantities.copy()

    max_iterations = 200
    iteration = 0

    while _has_remaining_demand(remaining) and iteration < max_iterations:
        iteration += 1

        best_pattern = _find_best_pattern_by_score(
            patterns, remaining, _calculate_pattern_score, size_priorities
        )
        if not best_pattern:
            logger.warning("greedy_classic: no best pattern found at iteration %d, breaking", iteration)
            break

        to_add = _determine_allocation_quantity(allocation, best_pattern.id, min_per_pattern)
        allocation[best_pattern.id] += to_add

        _update_remaining(remaining, best_pattern, to_add)

    if iteration >= max_iterations:
        logger.warning("greedy_classic: hit max_iterations=%d limit", max_iterations)

    logger.info("Greedy classic complete: %d iterations", iteration)
    return allocation


def greedy_overshoot(
    quantities: dict[str, int],
    patterns: list[Pattern],
    min_per_pattern: int,
    size_priorities: dict[str, float] | None = None,
) -> dict[int, int]:
    allocation = dict.fromkeys((p.id for p in patterns), 0)
    remaining = quantities.copy()

    max_iterations = 200
    iteration = 0

    while _has_remaining_demand(remaining) and iteration < max_iterations:
        iteration += 1

        best_pattern = _find_best_pattern_by_score(
            patterns, remaining, _calculate_greedy_score, size_priorities
        )
        if not best_pattern:
            logger.warning("greedy_overshoot: no best pattern found at iteration %d, breaking", iteration)
            break

        to_add = _determine_allocation_quantity(allocation, best_pattern.id, min_per_pattern)
        allocation[best_pattern.id] += to_add

        _update_remaining(remaining, best_pattern, to_add)

    if iteration >= max_iterations:
        logger.warning("greedy_overshoot: hit max_iterations=%d limit", max_iterations)

    logger.info("Greedy overshoot complete: %d iterations", iteration)
    return allocation


def calculate_total_excess(
    quantities: dict[str, int], allocation: dict[int, int], patterns: list[Pattern]
) -> int:
    produced = dict.fromkeys(quantities, 0)

    for pattern in patterns:
        count = allocation[pattern.id]
        if count > 0:
            for size, size_count in pattern.sizes.items():
                produced[size] = produced.get(size, 0) + (count * size_count)

    total_excess = 0
    for size in quantities:
        size_excess = max(0, produced[size] - quantities[size])
        total_excess += size_excess

    return total_excess
