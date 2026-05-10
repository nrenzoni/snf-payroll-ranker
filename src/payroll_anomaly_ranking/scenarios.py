from __future__ import annotations

from dataclasses import asdict, dataclass, field

from payroll_anomaly_ranking.columns import (
    PayCodeCategory,
    PayrollCol,
    ScenarioFamily,
    ShiftType,
    SNFRole,
)


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
    field: str = PayrollCol.GROSS_PAY
    multiplier: float = 1.0
    additive_shift: float = 0.0
    pay_code: str | None = None


@dataclass(frozen=True)
class QueueSimulationSpec:
    iterations: int = 100
    review_budget: int = 25
    score_threshold: float | None = None
    score_thresholds: tuple[float, ...] = ()
    adaptive_threshold_quantile: float | None = None
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


FUTURE_SCENARIO_CATALOG: dict[str, str] = {
    ScenarioFamily.AGENCY_FLOAT_LABOR: "Future: agency and float labor duplicate payment, allocation, and high-cost shift scenarios.",
    ScenarioFamily.CENSUS_ACUITY: "Future: census/acuity-adjusted staffing and payroll-per-resident-day scenarios.",
    ScenarioFamily.CREDENTIAL_LICENSE: "Future: credential, license, role, and pay eligibility mismatch scenarios.",
    ScenarioFamily.PBJ_CATEGORY: "Future: PBJ staffing category consistency scenarios.",
    ScenarioFamily.MEAL_BREAK_PREMIUM: "Future: missed meal break premium scenarios.",
    ScenarioFamily.LIFECYCLE: "Future: new hire orientation, termination, and final pay lifecycle scenarios.",
    ScenarioFamily.RETRO_RATE: "Future: retroactive pay and rate correction scenarios.",
    ScenarioFamily.UNION_POLICY: "Future: union or contract policy variation scenarios.",
    ScenarioFamily.NEW_CLIENT_BOOTSTRAP: "Future: new client facility bootstrap normalization scenarios.",
    ScenarioFamily.PAYROLL_CLOSE_ADJUSTMENT: "Future: payroll close/reopen manual adjustment concentration scenarios.",
}


def diagnostic_scenario_catalog() -> dict[str, ScenarioSpec]:
    catalog = {
        "baseline": ScenarioSpec(
            name="baseline",
            metadata={
                "scenario_family": ScenarioFamily.BASELINE,
                "status": "implemented",
                "description": "Multi-facility SNF baseline with realistic shift, timeclock, and premium variation.",
                "future_scenarios": FUTURE_SCENARIO_CATALOG,
            },
        ),
        "overtime-staffing-pressure": ScenarioSpec(
            name="overtime-staffing-pressure",
            seed_offset=10,
            anomaly_plan=AnomalyPlan(
                target_count=140,
                targeted_controls=(
                    TargetedAnomalyControl(
                        name="nursing-double-shift-pressure",
                        subgroup_filters={
                            PayrollCol.ROLE: [SNFRole.RN, SNFRole.LPN, SNFRole.CNA],
                            PayrollCol.SHIFT_TYPE: [
                                ShiftType.DAY,
                                ShiftType.EVENING,
                                ShiftType.NIGHT,
                            ],
                        },
                        target_count=110,
                    ),
                ),
            ),
            metadata={
                "scenario_family": ScenarioFamily.OVERTIME_STAFFING_PRESSURE,
                "status": "implemented",
                "description": "Overtime, double-shift, rest-gap, and staffing pressure approval case study.",
                "future_scenarios": FUTURE_SCENARIO_CATALOG,
            },
        ),
        "premium-mismatch": ScenarioSpec(
            name="premium-mismatch",
            seed_offset=20,
            anomaly_plan=AnomalyPlan(
                target_count=130,
                targeted_controls=(
                    TargetedAnomalyControl(
                        name="unsupported-shift-differentials",
                        subgroup_filters={
                            PayrollCol.PAY_CODE_CATEGORY: [
                                PayCodeCategory.SHIFT_DIFF,
                                PayCodeCategory.WEEKEND_DIFF,
                            ],
                        },
                        target_count=100,
                    ),
                ),
            ),
            metadata={
                "scenario_family": ScenarioFamily.PREMIUM_MISMATCH,
                "status": "implemented",
                "description": "Premium pay and shift differential mismatch approval case study.",
                "future_scenarios": FUTURE_SCENARIO_CATALOG,
            },
        ),
        "agency-float-labor-future": ScenarioSpec(
            name="agency-float-labor-future",
            metadata={
                "scenario_family": ScenarioFamily.AGENCY_FLOAT_LABOR,
                "status": "documented_future",
                "description": FUTURE_SCENARIO_CATALOG[
                    ScenarioFamily.AGENCY_FLOAT_LABOR
                ],
            },
        ),
    }
    legacy_aliases = {
        "rule-friendly": "premium-mismatch",
        "statistical-friendly": "overtime-staffing-pressure",
        "ml-friendly": "premium-mismatch",
        "exposure-heavy": "overtime-staffing-pressure",
        "subgroup-drift": "overtime-staffing-pressure",
        "calendar-drift": "premium-mismatch",
        "queue-stress": "overtime-staffing-pressure",
    }
    for alias, target in legacy_aliases.items():
        base = catalog[target]
        catalog[alias] = ScenarioSpec(
            name=alias,
            seed_offset=base.seed_offset + len(alias),
            anomaly_plan=base.anomaly_plan,
            metadata={**base.metadata, "alias_for": target},
        )
    return catalog


def diagnostic_scenario_presets(
    names: tuple[str, ...] | None = None,
) -> dict[str, ScenarioSpec]:
    catalog = diagnostic_scenario_catalog()
    if names is None:
        return catalog
    return {name: catalog[name] for name in names}
