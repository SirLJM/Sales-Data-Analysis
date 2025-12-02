import json
import os
from dataclasses import asdict, dataclass

from utils.settings_manager import load_settings


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
    quantities: dict[str, int], patterns: list[Pattern], min_per_pattern: int
) -> dict[int, int] | None:
    best_solution = None
    best_excess = float("inf")
    max_total = sum(quantities.values()) * 2
    min_patterns = max(quantities.values()) // 2

    for total_patterns in range(min_patterns, min(max_total + 1, min_patterns + 100)):
        solution = find_allocation_for_total(quantities, patterns, total_patterns, min_per_pattern)

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
        for size, size_count in pattern.sizes.items():
            produced[size] = produced.get(size, 0) + (count * size_count)
    return produced


def _find_violations(
    allocation: dict[int, int], patterns: list[Pattern], min_per_pattern: int
) -> list[tuple]:
    violations = []
    for pattern in patterns:
        count = allocation.get(pattern.id, 0)
        if 0 < count < min_per_pattern:
            violations.append((pattern.name, count))
    return violations


def optimize_patterns(
    quantities: dict[str, int],
    patterns: list[Pattern],
    min_per_pattern: int = get_min_order_per_pattern(),
) -> dict:
    if not patterns or not any(quantities.values()):
        return _get_empty_result(quantities)

    best_solution = _find_best_solution(quantities, patterns, min_per_pattern)
    if not best_solution:
        best_solution = greedy_overshoot(quantities, patterns, min_per_pattern)

    produced = _calculate_production(best_solution, patterns, quantities)
    excess = {size: produced[size] - quantities[size] for size in quantities}
    min_violations = _find_violations(best_solution, patterns, min_per_pattern)

    return {
        "allocation": best_solution,
        "produced": produced,
        "excess": excess,
        "total_patterns": sum(best_solution.values()),
        "total_excess": sum(excess.values()),
        "all_covered": all(produced[size] >= quantities[size] for size in quantities),
        "min_order_violations": min_violations,
    }


def _calculate_pattern_score(pattern: Pattern, remaining: dict[str, int]) -> int:
    score = 0
    for size, count in pattern.sizes.items():
        if remaining.get(size, 0) > 0:
            score += min(count, remaining[size]) * 10
        else:
            score -= count
    return score


def _calculate_greedy_score(pattern: Pattern, remaining: dict[str, int]) -> float:
    score = 0.0
    for size, count in pattern.sizes.items():
        if remaining.get(size, 0) > 0:
            score += min(count, remaining[size]) * 100
            score += remaining[size] * 10
        else:
            score -= count * 1
    return score


def _find_best_pattern_by_score(
    patterns: list[Pattern], remaining: dict[str, int], score_func
) -> Pattern | None:
    best_pattern = None
    best_score = -float("inf")

    for pattern in patterns:
        score = score_func(pattern, remaining)
        if score > best_score:
            best_score = score
            best_pattern = pattern

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
        remaining[size] = remaining.get(size, 0) - (count * quantity)


def find_allocation_for_total(
    quantities: dict[str, int], patterns: list[Pattern], total: int, min_per_pattern: int
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
            valid_patterns, remaining, _calculate_pattern_score
        )
        if not best_pattern:
            break

        to_allocate = min(min_per_pattern, total - patterns_used)
        if allocation[best_pattern.id] > 0:
            to_allocate = 1

        allocation[best_pattern.id] += to_allocate
        patterns_used += to_allocate
        _update_remaining(remaining, best_pattern, to_allocate)

    if all(remaining.get(size, 0) <= 0 for size in quantities):
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


def greedy_overshoot(
    quantities: dict[str, int], patterns: list[Pattern], min_per_pattern: int
) -> dict[int, int]:
    allocation = dict.fromkeys((p.id for p in patterns), 0)
    remaining = quantities.copy()

    max_iterations = 200
    iteration = 0

    while _has_remaining_demand(remaining) and iteration < max_iterations:
        iteration += 1

        best_pattern = _find_best_pattern_by_score(patterns, remaining, _calculate_greedy_score)
        if not best_pattern:
            break

        to_add = _determine_allocation_quantity(allocation, best_pattern.id, min_per_pattern)
        allocation[best_pattern.id] += to_add
        _update_remaining(remaining, best_pattern, to_add)

    return allocation


def calculate_total_excess(
    quantities: dict[str, int], allocation: dict[int, int], patterns: list[Pattern]
) -> int:
    produced = dict.fromkeys(quantities, 0)

    for pattern in patterns:
        count = allocation[pattern.id]
        for size, size_count in pattern.sizes.items():
            produced[size] = produced.get(size, 0) + (count * size_count)

    return sum(max(0, produced[size] - quantities[size]) for size in quantities)
