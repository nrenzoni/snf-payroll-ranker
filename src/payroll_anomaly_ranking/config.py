from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from payroll_anomaly_ranking.columns import ScoreCol


@dataclass(frozen=True)
class PayrollConfig:
    seed: int = 42
    employee_count: int = 650
    pay_periods: int = 26
    review_budgets: tuple[int, ...] = (10, 25, 50)
    hybrid_weights: dict[str, float] = field(
        default_factory=lambda: {
            ScoreCol.RULE_SCORE: 0.30,
            ScoreCol.HISTORY_SCORE: 0.22,
            ScoreCol.PEER_SCORE: 0.18,
            ScoreCol.ML_SCORE: 0.20,
            ScoreCol.EXPOSURE_SCORE: 0.10,
        }
    )
    data_dir: Path = Path("data/synthetic")
    output_dir: Path = Path("outputs")

    @property
    def periods_per_year(self) -> int:
        return 26
