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
        },
    )
    uncertainty_component_weights: dict[str, float] = field(
        default_factory=lambda: {
            ScoreCol.ENSEMBLE_DISAGREEMENT_UNCERTAINTY: 0.18,
            ScoreCol.BOOTSTRAP_INTERVAL_UNCERTAINTY: 0.14,
            ScoreCol.EXPECTED_GROSS_PAY_INTERVAL_WIDTH: 0.14,
            ScoreCol.PEER_GROUP_UNCERTAINTY: 0.14,
            ScoreCol.EMPLOYEE_HISTORY_UNCERTAINTY: 0.12,
            ScoreCol.DATA_QUALITY_UNCERTAINTY: 0.14,
            ScoreCol.OOD_UNCERTAINTY: 0.14,
        },
    )
    uncertainty_bucket_thresholds: tuple[float, float] = (0.35, 0.65)
    reference_window_periods: int = 6
    bootstrap_samples: int = 8
    bootstrap_min_reference_rows: int = 40
    bootstrap_percentiles: tuple[float, float] = (10.0, 90.0)
    ood_rare_pay_code_threshold: int = 3
    ood_nearest_neighbor_percentile: float = 0.90
    data_dir: Path = Path("data/synthetic")
    output_dir: Path = Path("outputs")

    @property
    def periods_per_year(self) -> int:
        return 26
