from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from payroll_anomaly_ranking.columns import ScoreCol


@dataclass(frozen=True)
class PayrollConfig:
    seed: int = 42
    employee_count: int = 650
    pay_periods: int = 26
    facility_count: int = 6
    shifts_per_employee_per_period: float = 4.5
    review_budgets: tuple[int, ...] = (10, 25, 50)
    employee_cycle_review_budget_percents: tuple[float, ...] | None = None
    hybrid_weights: dict[ScoreCol, float] = field(
        default_factory=lambda: {
            ScoreCol.RULE_SCORE: 0.30,
            ScoreCol.HISTORY_SCORE: 0.22,
            ScoreCol.PEER_SCORE: 0.18,
            ScoreCol.ML_SCORE: 0.20,
            ScoreCol.EXPOSURE_SCORE: 0.10,
        },
    )
    uncertainty_component_weights: dict[ScoreCol, float] = field(
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
    ltr_num_threads: int = 2
    data_dir: Path = Path("data/synthetic")
    output_dir: Path = Path("outputs")

    @property
    def periods_per_year(self) -> int:
        return 26


@dataclass(frozen=True)
class SNFPayPolicyConfig:
    evening_diff_rate: float = 2.25
    night_diff_rate: float = 3.50
    weekend_diff_rate: float = 2.00
    overtime_multiplier: float = 1.5
    overtime_daily_hours: float = 8.0
    rest_gap_warning_hours: float = 8.0
    paid_vs_scheduled_warning_hours: float = 1.5
    gross_pay_threshold: float = 1_500.0
    total_hours_threshold: float = 16.0
    overtime_hours_threshold: float = 8.0
    premium_dollars_threshold: float = 100.0
    paid_vs_scheduled_threshold: float = 2.0
    facility_variance_threshold: float = 0.20


def validate_snf_config(
    config: PayrollConfig = PayrollConfig(),
    policy: SNFPayPolicyConfig = SNFPayPolicyConfig(),
) -> None:
    if config.employee_count <= 0:
        raise ValueError("employee_count must be positive")
    if config.facility_count <= 0:
        raise ValueError("facility_count must be positive")
    if config.pay_periods < 4:
        raise ValueError("pay_periods must be at least 4 for temporal evaluation")
    if not config.review_budgets or min(config.review_budgets) <= 0:
        raise ValueError("review_budgets must contain positive values")
    if config.employee_cycle_review_budget_percents is not None and (
        not config.employee_cycle_review_budget_percents
        or min(config.employee_cycle_review_budget_percents) <= 0
        or max(config.employee_cycle_review_budget_percents) > 1
    ):
        raise ValueError(
            "employee_cycle_review_budget_percents must contain values in (0, 1]",
        )
    if config.shifts_per_employee_per_period <= 0:
        raise ValueError("shifts_per_employee_per_period must be positive")
    if policy.overtime_multiplier < 1:
        raise ValueError("overtime_multiplier must be at least 1")
    if policy.rest_gap_warning_hours <= 0:
        raise ValueError("rest_gap_warning_hours must be positive")
    if config.ltr_num_threads <= 0:
        raise ValueError("ltr_num_threads must be positive")
