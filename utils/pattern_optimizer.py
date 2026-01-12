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

    excluded_sizes = {
        size for size, qty in quantities.items()
        if size_sales_history.get(size, 0) < MIN_SALES_THRESHOLD
    }

    return {k: v for k, v in quantities.items() if k not in excluded_sizes}, list(excluded_sizes)


def calculate_size_priorities(size_sales_history: dict[str, int] | None) -> dict[str, float] | None:
    if not size_sales_history:
        return None

    total_sales = sum(size_sales_history.values())
    if total_sales == 0:
        return None

    return {size: sales / total_sales for size, sales in size_sales_history.items()}


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


def _get_greedy_algorithm(algorithm_mode: str):
    return greedy_classic if algorithm_mode == "greedy_classic" else greedy_overshoot


def _build_optimization_result(
    allocation: dict[int, int],
    patterns: list[Pattern],
    filtered_quantities: dict[str, int],
    excluded_sizes: list[str],
    min_per_pattern: int,
    algorithm_mode: str,
) -> dict:
    produced = _calculate_production(allocation, patterns, filtered_quantities)
    excess = {size: produced[size] - filtered_quantities[size] for size in filtered_quantities}

    for size in excluded_sizes:
        produced[size] = 0
        excess[size] = 0

    return {
        "allocation": allocation,
        "produced": produced,
        "excess": excess,
        "total_patterns": sum(allocation.values()),
        "total_excess": sum(excess.values()),
        "all_covered": all(produced.get(s, 0) >= filtered_quantities.get(s, 0) for s in filtered_quantities),
        "min_order_violations": _find_violations(allocation, patterns, min_per_pattern),
        "algorithm_used": algorithm_mode,
        "excluded_sizes": excluded_sizes,
    }


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
        greedy_func = _get_greedy_algorithm(algorithm_mode)
        best_solution = greedy_func(filtered_quantities, patterns, min_per_pattern, size_priorities)

    result = _build_optimization_result(
        best_solution, patterns, filtered_quantities, excluded_sizes, min_per_pattern, algorithm_mode
    )
    logger.info("Optimization result: total_patterns=%d, total_excess=%d, all_covered=%s",
                result["total_patterns"], result["total_excess"], result["all_covered"])
    return result


def _calculate_size_score(
    remaining_size: int,
    count: int,
    base_multiplier: int,
    priority: float | None,
    priority_multiplier: int,
    remaining_bonus: int = 0,
) -> float:
    if remaining_size <= 0:
        return -count

    base_score = min(count, remaining_size) * base_multiplier + remaining_size * remaining_bonus
    if priority is not None:
        return base_score + priority * count * priority_multiplier
    return base_score


def _calculate_pattern_score(
    pattern: Pattern, remaining: dict[str, int], size_priorities: dict[str, float] | None = None
) -> float:
    return sum(
        _calculate_size_score(
            remaining.get(size, 0), count, 10,
            size_priorities.get(size) if size_priorities else None, 5
        )
        for size, count in pattern.sizes.items()
    )


def _calculate_greedy_score(
    pattern: Pattern, remaining: dict[str, int], size_priorities: dict[str, float] | None = None
) -> float:
    return sum(
        _calculate_size_score(
            remaining.get(size, 0), count, 100,
            size_priorities.get(size) if size_priorities else None, 50, 10
        )
        for size, count in pattern.sizes.items()
    )


def _find_best_pattern_by_score(
    patterns: list[Pattern],
    remaining: dict[str, int],
    score_func,
    size_priorities: dict[str, float] | None = None,
) -> Pattern | None:
    if not patterns:
        logger.warning("No best pattern found!")
        return None

    return max(patterns, key=lambda p: score_func(p, remaining, size_priorities))


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
    return any(qty > 0 for qty in remaining.values())


def _determine_allocation_quantity(
    allocation: dict[int, int], pattern_id: int, min_per_pattern: int
) -> int:
    return min_per_pattern if allocation[pattern_id] == 0 else 1


def _greedy_allocate(
    quantities: dict[str, int],
    patterns: list[Pattern],
    min_per_pattern: int,
    score_func,
    algorithm_name: str,
    size_priorities: dict[str, float] | None = None,
) -> dict[int, int]:
    allocation = dict.fromkeys((p.id for p in patterns), 0)
    remaining = quantities.copy()
    max_iterations = 200
    iteration = 0

    for iteration in range(1, max_iterations + 1):
        if not _has_remaining_demand(remaining):
            break

        best_pattern = _find_best_pattern_by_score(patterns, remaining, score_func, size_priorities)
        if not best_pattern:
            logger.warning("%s: no best pattern found at iteration %d, breaking", algorithm_name, iteration)
            break

        to_add = _determine_allocation_quantity(allocation, best_pattern.id, min_per_pattern)
        allocation[best_pattern.id] += to_add
        _update_remaining(remaining, best_pattern, to_add)
    else:
        logger.warning("%s: hit max_iterations=%d limit", algorithm_name, max_iterations)

    logger.info("%s complete: %d iterations", algorithm_name, iteration)
    return allocation


def greedy_classic(
    quantities: dict[str, int],
    patterns: list[Pattern],
    min_per_pattern: int,
    size_priorities: dict[str, float] | None = None,
) -> dict[int, int]:
    return _greedy_allocate(
        quantities, patterns, min_per_pattern, _calculate_pattern_score, "greedy_classic", size_priorities
    )


def greedy_overshoot(
    quantities: dict[str, int],
    patterns: list[Pattern],
    min_per_pattern: int,
    size_priorities: dict[str, float] | None = None,
) -> dict[int, int]:
    return _greedy_allocate(
        quantities, patterns, min_per_pattern, _calculate_greedy_score, "greedy_overshoot", size_priorities
    )


def calculate_total_excess(
    quantities: dict[str, int], allocation: dict[int, int], patterns: list[Pattern]
) -> int:
    produced = _calculate_production(allocation, patterns, quantities)
    return sum(max(0, produced[size] - quantities[size]) for size in quantities)
