from __future__ import annotations

from dataclasses import asdict, dataclass, field

from payroll_anomaly_ranking.columns import PayrollCol


@dataclass(frozen=True)
class TargetedAnomalyControl:
    name: str = "target"
    start_period: int | None = None
    end_period: int | None = None
    subgroup_filters: dict[str, object] = field(default_factory=dict)
    category_weights: dict[str, float] = field(default_factory=dict)
    target_count: int | None = None
    propensity_multiplier: float = 1.0
    severity_multipliers: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class AnomalyPlan:
    category_weights: dict[str, float] = field(default_factory=dict)
    target_count: int | None = None
    severity_multipliers: dict[str, float] = field(default_factory=dict)
    targeted_controls: tuple[TargetedAnomalyControl, ...] = ()


@dataclass(frozen=True)
class DriftPlan:
    name: str = "drift"
    start_period: int | None = None
    end_period: int | None = None
    subgroup_filters: dict[str, object] = field(default_factory=dict)
    pay_code_mix_shift: dict[str, float] = field(default_factory=dict)
    overtime_multiplier: float | None = None
    deduction_multiplier: float | None = None
    gross_pay_multiplier: float | None = None
    payroll_total_multiplier: float | None = None
    multiplier_noise: float = 0.0


@dataclass(frozen=True)
class ChangePointEvent:
    name: str
    start_period: int
    end_period: int | None = None
    subgroup_filters: dict[str, object] = field(default_factory=dict)
    field: str = "gross_pay"
    multiplier: float = 1.0
    additive_shift: float = 0.0
    pay_code: str | None = None


@dataclass(frozen=True)
class QueueSimulationSpec:
    iterations: int = 100
    review_budget: int = 25
    score_threshold: float | None = None
    fixed_capacity: int | None = None
    period_capacity: dict[int, int] = field(default_factory=dict)
    period_capacity_multipliers: dict[int, float] = field(default_factory=dict)
    capacity_sd: float = 0.0
    seed: int = 42
    scenario: str = "baseline"


@dataclass(frozen=True)
class ScenarioSpec:
    name: str = "baseline"
    seed_offset: int = 0
    anomaly_plan: AnomalyPlan | None = None
    drift_plans: tuple[DriftPlan, ...] = ()
    change_points: tuple[ChangePointEvent, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, object]:
        return asdict(self)


def diagnostic_scenario_catalog() -> dict[str, ScenarioSpec]:
    return {
        "baseline": ScenarioSpec(
            name="baseline",
            metadata={"regime": "baseline", "description": "Default synthetic world"},
        ),
        "rule-friendly": ScenarioSpec(
            name="rule-friendly",
            seed_offset=10,
            anomaly_plan=AnomalyPlan(
                category_weights={
                    "missing_deduction": 0.45,
                    "negative_net_pay": 0.25,
                    "pay_after_termination": 0.20,
                    "duplicate_payment": 0.10,
                },
                target_count=130,
            ),
            metadata={"regime": "rule-friendly"},
        ),
        "statistical-friendly": ScenarioSpec(
            name="statistical-friendly",
            seed_offset=20,
            anomaly_plan=AnomalyPlan(
                category_weights={
                    "gross_pay_spike": 0.45,
                    "retro_pay_outlier": 0.30,
                    "overtime_spike": 0.25,
                },
                target_count=130,
                severity_multipliers={
                    "gross_pay_spike": 1.6,
                    "retro_pay_outlier": 1.5,
                    "overtime_spike": 1.4,
                },
            ),
            metadata={"regime": "statistical-friendly"},
        ),
        "ml-friendly": ScenarioSpec(
            name="ml-friendly",
            seed_offset=30,
            anomaly_plan=AnomalyPlan(
                category_weights={
                    "new_employee_large_payment": 0.45,
                    "department_payroll_spike": 0.35,
                    "incorrect_pay_rate": 0.20,
                },
                target_count=120,
            ),
            drift_plans=(
                DriftPlan(
                    name="rare-combination-drift",
                    start_period=8,
                    subgroup_filters={PayrollCol.LOCATION: "Remote"},
                    pay_code_mix_shift={"SPEC": 0.7, "ADJX": 0.3},
                    gross_pay_multiplier=1.10,
                ),
            ),
            metadata={"regime": "ml-friendly"},
        ),
        "exposure-heavy": ScenarioSpec(
            name="exposure-heavy",
            seed_offset=40,
            anomaly_plan=AnomalyPlan(
                category_weights={
                    "duplicate_payment": 0.35,
                    "gross_pay_spike": 0.30,
                    "incorrect_pay_rate": 0.20,
                    "retro_pay_outlier": 0.15,
                },
                target_count=100,
                severity_multipliers={
                    "duplicate_payment": 1.8,
                    "gross_pay_spike": 2.0,
                    "incorrect_pay_rate": 1.7,
                    "retro_pay_outlier": 1.8,
                },
            ),
            metadata={"regime": "exposure-heavy"},
        ),
        "subgroup-drift": ScenarioSpec(
            name="subgroup-drift",
            seed_offset=50,
            anomaly_plan=AnomalyPlan(
                target_count=100,
                targeted_controls=(
                    TargetedAnomalyControl(
                        name="operations-late-drift",
                        start_period=7,
                        subgroup_filters={PayrollCol.DEPARTMENT: "Operations"},
                        category_weights={
                            "overtime_spike": 0.55,
                            "gross_pay_spike": 0.30,
                            "missing_deduction": 0.15,
                        },
                        target_count=55,
                        severity_multipliers={"overtime_spike": 1.5},
                    ),
                ),
            ),
            metadata={"regime": "subgroup-drift"},
        ),
        "calendar-drift": ScenarioSpec(
            name="calendar-drift",
            seed_offset=60,
            anomaly_plan=AnomalyPlan(
                target_count=105,
                targeted_controls=(
                    TargetedAnomalyControl(
                        name="late-calendar-outliers",
                        start_period=9,
                        category_weights={
                            "retro_pay_outlier": 0.45,
                            "department_payroll_spike": 0.35,
                            "gross_pay_spike": 0.20,
                        },
                        propensity_multiplier=2.5,
                        severity_multipliers={"department_payroll_spike": 1.5},
                    ),
                ),
            ),
            change_points=(
                ChangePointEvent(
                    name="late-period-special-pay-code",
                    start_period=9,
                    field=PayrollCol.GROSS_PAY,
                    multiplier=1.08,
                    pay_code="ADJX",
                ),
            ),
            metadata={"regime": "calendar-drift"},
        ),
        "queue-stress": ScenarioSpec(
            name="queue-stress",
            seed_offset=70,
            anomaly_plan=AnomalyPlan(
                target_count=170,
                category_weights={
                    "duplicate_payment": 0.25,
                    "gross_pay_spike": 0.25,
                    "overtime_spike": 0.25,
                    "missing_deduction": 0.25,
                },
                severity_multipliers={
                    "duplicate_payment": 1.5,
                    "gross_pay_spike": 1.5,
                },
            ),
            metadata={
                "regime": "queue-stress",
                "queue_capacity_multipliers": {8: 0.6, 9: 0.6, 10: 0.7},
            },
        ),
    }


def diagnostic_scenario_presets(
    names: tuple[str, ...] | None = None,
) -> dict[str, ScenarioSpec]:
    catalog = diagnostic_scenario_catalog()
    if names is None:
        return catalog
    return {name: catalog[name] for name in names}
