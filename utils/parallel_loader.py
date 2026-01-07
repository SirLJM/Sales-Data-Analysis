from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, TypeVar

from utils.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")
R = TypeVar("R")

PARALLEL_LOAD_WORKERS = 4


def parallel_load(
    items: list[T],
    load_func: Callable[[T], R | None],
    max_workers: int = PARALLEL_LOAD_WORKERS,
    desc: str = "Loading",
) -> list[R]:
    if not items:
        return []

    if len(items) == 1:
        result = load_func(items[0])
        return [result] if result is not None else []

    results: list[R] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(load_func, item): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.warning("%s failed for %s: %s", desc, item, e)
    return results
