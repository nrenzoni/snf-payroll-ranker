from __future__ import annotations

import os


def notebook_fast_mode() -> bool:
    """Return whether notebook execution should use diagnostic fast mode."""
    enabled = os.getenv("NOTEBOOK_FAST") == "1"
    if enabled:
        print(
            "NOTEBOOK_FAST=1: using reduced diagnostic workload for execution checks.",
        )
    return enabled
