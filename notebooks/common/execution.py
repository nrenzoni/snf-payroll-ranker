from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path


def load_cached_or_calc[T](
    cache_path: Path,
    calc: Callable[[], T],
    *,
    read: Callable[[Path], T],
    write: Callable[[Path, T], None],
) -> T:
    """Load a local cache artifact or calculate and persist it.

    Delete the cache file or directory to force recalculation on the next run.
    """
    if cache_path.exists():
        print(f"Loading cached result from {cache_path}")
        return read(cache_path)

    result = calc()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    write(cache_path, result)
    print(f"Cached result at {cache_path}")
    return result


def notebook_validation_mode() -> bool:
    """Return whether notebook execution should use validation-mode workload."""
    enabled = os.getenv("NOTEBOOK_VALIDATE") == "1"
    if enabled:
        print(
            "NOTEBOOK_VALIDATE=1: using reduced execution-check workload.",
        )
    return enabled
