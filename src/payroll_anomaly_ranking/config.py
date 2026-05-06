from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class PayrollConfig:
    seed: int = 42
    employee_count: int = 650
    pay_periods: int = 26
    review_budgets: tuple[int, ...] = (10, 25, 50)
    hybrid_weights: dict[str, float] = field(
        default_factory=lambda: {
            "rule_score": 0.30,
            "history_score": 0.22,
            "peer_score": 0.18,
            "ml_score": 0.20,
            "dollar_score": 0.10,
        }
    )
    data_dir: Path = Path("data/synthetic")
    output_dir: Path = Path("outputs")

    @property
    def periods_per_year(self) -> int:
        return 26
