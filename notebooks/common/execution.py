from __future__ import annotations

import os


def notebook_validation_mode() -> bool:
    """Return whether notebook execution should use validation-mode workload."""
    enabled = os.getenv("NOTEBOOK_VALIDATE") == "1"
    if enabled:
        print(
            "NOTEBOOK_VALIDATE=1: using reduced execution-check workload.",
        )
    return enabled
