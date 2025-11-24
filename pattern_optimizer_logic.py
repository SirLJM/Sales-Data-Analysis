import json
import os
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional


@dataclass
class Pattern:
    id: int
    name: str
    sizes: Dict[str, int]

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class PatternSet:
    id: int
    name: str
    size_names: List[str]
    patterns: List[Pattern]

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "size_names": self.size_names,
            "patterns": [p.to_dict() for p in self.patterns],
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            name=data["name"],
            size_names=data.get("size_names", ["XL", "L", "M", "S", "XS"]),
            patterns=[Pattern.from_dict(p) for p in data["patterns"]],
        )


PATTERN_SETS_FILE = "saved_pattern_sets.json"
MIN_ORDER_PER_PATTERN = 5


def load_pattern_sets() -> List[PatternSet]:
    if os.path.exists(PATTERN_SETS_FILE):
        try:
            with open(PATTERN_SETS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [PatternSet.from_dict(ps) for ps in data]
        except (json.JSONDecodeError, KeyError, ValueError):
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


def save_pattern_sets(pattern_sets: List[PatternSet]):
    with open(PATTERN_SETS_FILE, "w", encoding="utf-8") as f:
        json.dump([ps.to_dict() for ps in pattern_sets], f, indent=2)


def optimize_patterns(
    quantities: Dict[str, int],
    patterns: List[Pattern],
    min_per_pattern: int = MIN_ORDER_PER_PATTERN,
) -> Dict:
    if not patterns or not any(quantities.values()):
        return {
            "allocation": {},
            "produced": {size: 0 for size in quantities},
            "excess": {size: 0 for size in quantities},
            "total_patterns": 0,
            "total_excess": 0,
            "all_covered": False,
            "min_order_violations": [],
        }

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

    if not best_solution:
        best_solution = greedy_overshoot(quantities, patterns, min_per_pattern)

    allocation: Dict[int, int] = best_solution
    produced: Dict[str, int] = {size: 0 for size in quantities}

    for pattern in patterns:
        count = allocation.get(pattern.id, 0)
        for size, size_count in pattern.sizes.items():
            produced[size] = produced.get(size, 0) + (count * size_count)

    excess = {size: produced[size] - quantities[size] for size in quantities}
    total_patterns = sum(allocation.values())
    total_excess = sum(excess.values())

    min_violations: List[tuple] = []
    for pattern in patterns:
        count = allocation.get(pattern.id, 0)
        if 0 < count < min_per_pattern:
            min_violations.append((pattern.name, count))

    return {
        "allocation": allocation,
        "produced": produced,
        "excess": excess,
        "total_patterns": total_patterns,
        "total_excess": total_excess,
        "all_covered": all(produced[size] >= quantities[size] for size in quantities),
        "min_order_violations": min_violations,
    }


def find_allocation_for_total(
    quantities: Dict[str, int], patterns: List[Pattern], total: int, min_per_pattern: int
) -> Optional[Dict[int, int]]:
    allocation = {p.id: 0 for p in patterns}
    remaining = quantities.copy()
    patterns_used = 0

    while patterns_used < total:
        best_pattern = None
        best_score = -float("inf")

        for pattern in patterns:
            if patterns_used + min_per_pattern > total:
                if allocation[pattern.id] == 0:
                    continue

            score = 0
            for size, count in pattern.sizes.items():
                if remaining.get(size, 0) > 0:
                    score += min(count, remaining[size]) * 10
                else:
                    score -= count

            if score > best_score:
                best_score = score
                best_pattern = pattern

        if best_pattern:
            to_allocate = min(min_per_pattern, total - patterns_used)
            if allocation[best_pattern.id] > 0:
                to_allocate = 1

            allocation[best_pattern.id] += to_allocate
            patterns_used += to_allocate

            for size, count in best_pattern.sizes.items():
                remaining[size] = remaining.get(size, 0) - (count * to_allocate)
        else:
            break

    if all(remaining.get(size, 0) <= 0 for size in quantities):
        return allocation

    return None


def greedy_overshoot(
    quantities: Dict[str, int], patterns: List[Pattern], min_per_pattern: int
) -> Dict[int, int]:
    allocation = {p.id: 0 for p in patterns}
    remaining = quantities.copy()

    max_iterations = 200
    iteration = 0

    while any(remaining[size] > 0 for size in remaining) and iteration < max_iterations:
        iteration += 1
        best_pattern = None
        best_score = -float("inf")

        for pattern in patterns:
            score = 0
            for size, count in pattern.sizes.items():
                if remaining.get(size, 0) > 0:
                    score += min(count, remaining[size]) * 100
                    score += remaining[size] * 10
                else:
                    score -= count * 1

            if score > best_score:
                best_score = score
                best_pattern = pattern

        if best_pattern:
            if allocation[best_pattern.id] == 0:
                to_add = min_per_pattern
            else:
                to_add = 1

            allocation[best_pattern.id] += to_add
            for size, count in best_pattern.sizes.items():
                remaining[size] = remaining.get(size, 0) - (count * to_add)
        else:
            break

    return allocation


def calculate_total_excess(
    quantities: Dict[str, int], allocation: Dict[int, int], patterns: List[Pattern]
) -> int:
    produced = {size: 0 for size in quantities}

    for pattern in patterns:
        count = allocation[pattern.id]
        for size, size_count in pattern.sizes.items():
            produced[size] = produced.get(size, 0) + (count * size_count)

    return sum(max(0, produced[size] - quantities[size]) for size in quantities)
