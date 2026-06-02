from __future__ import annotations

from dataclasses import asdict, dataclass, field

from payroll_anomaly_ranking.columns import (
    PayrollCol,
    ScenarioFamily,
    SNFAnomalyCategory,
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
class ScenarioGeneratorControls:
    timekeeping_noise_multiplier: float = 1.0
    facility_heterogeneity_multiplier: float = 1.0
    base_rate_variation_multiplier: float = 1.0
    anomaly_dollar_multiplier: float = 1.0
    residual_target_multiplier: float = 1.0
    observed_review_bias_multiplier: float = 1.0


@dataclass(frozen=True)
class ScenarioSpec:
    name: str = "baseline"
    seed_offset: int = 0
    anomaly_plan: AnomalyPlan | None = None
    drift_plans: tuple[DriftPlan, ...] = ()
    change_points: tuple[ChangePointEvent, ...] = ()
    generator_controls: ScenarioGeneratorControls | None = None
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


def implemented_dgp_scenario_catalog() -> dict[str, ScenarioSpec]:
    return {
        "baseline-operations": ScenarioSpec(
            name="baseline-operations",
            metadata={
                "scenario_family": ScenarioFamily.BASELINE,
                "status": "implemented",
                "display_name": "Baseline operations",
                "what_changes": "default issue mix, moderate noise",
                "description": "Reference SNF payroll world with moderate timekeeping noise, facility variation, and mixed residual anomaly families.",
            },
        ),
        "high-timekeeping-noise": ScenarioSpec(
            name="high-timekeeping-noise",
            seed_offset=10,
            anomaly_plan=AnomalyPlan(
                target_count=170,
                category_weights={
                    str(SNFAnomalyCategory.PAID_VS_SCHEDULED_MISMATCH): 0.40,
                    str(SNFAnomalyCategory.DUPLICATE_PREMIUM): 0.18,
                    str(SNFAnomalyCategory.UNSUPPORTED_SHIFT_DIFFERENTIAL): 0.17,
                    str(SNFAnomalyCategory.CROSS_FACILITY_ALLOCATION): 0.13,
                    str(SNFAnomalyCategory.RETRO_RATE_MISMATCH): 0.07,
                    str(SNFAnomalyCategory.OVERTIME_DOUBLE_SHIFT): 0.05,
                },
                severity_multipliers={
                    "paid_vs_scheduled_mismatch": 1.15,
                    "duplicate_premium": 1.05,
                },
            ),
            generator_controls=ScenarioGeneratorControls(
                timekeeping_noise_multiplier=1.75,
                residual_target_multiplier=1.15,
            ),
            metadata={
                "scenario_family": ScenarioFamily.BASELINE,
                "status": "implemented",
                "display_name": "High timekeeping noise",
                "what_changes": "more missing punches, late edits, paid-vs-scheduled mismatches",
                "description": "Higher ambient timekeeping friction creates more ambiguous residual payroll discrepancies after hard-rule gating.",
            },
        ),
        "high-facility-heterogeneity": ScenarioSpec(
            name="high-facility-heterogeneity",
            seed_offset=20,
            anomaly_plan=AnomalyPlan(
                severity_multipliers={
                    "cross_facility_allocation": 1.20,
                    "retro_rate_mismatch": 1.10,
                },
            ),
            generator_controls=ScenarioGeneratorControls(
                facility_heterogeneity_multiplier=1.85,
                base_rate_variation_multiplier=1.45,
            ),
            metadata={
                "scenario_family": ScenarioFamily.BASELINE,
                "status": "implemented",
                "display_name": "High facility heterogeneity",
                "what_changes": "facilities differ more in payroll hygiene and pay norms",
                "description": "Facility-specific pressure, maturity, and pay norms vary more strongly, widening peer-context differences across the synthetic operator.",
            },
        ),
        "heavy-dollar-tail": ScenarioSpec(
            name="heavy-dollar-tail",
            seed_offset=30,
            anomaly_plan=AnomalyPlan(
                target_count=115,
                category_weights={
                    str(SNFAnomalyCategory.PAID_VS_SCHEDULED_MISMATCH): 0.16,
                    str(SNFAnomalyCategory.DUPLICATE_PREMIUM): 0.07,
                    str(SNFAnomalyCategory.UNSUPPORTED_SHIFT_DIFFERENTIAL): 0.16,
                    str(SNFAnomalyCategory.CROSS_FACILITY_ALLOCATION): 0.20,
                    str(SNFAnomalyCategory.RETRO_RATE_MISMATCH): 0.21,
                    str(SNFAnomalyCategory.OVERTIME_DOUBLE_SHIFT): 0.20,
                },
                severity_multipliers={
                    "cross_facility_allocation": 1.55,
                    "retro_rate_mismatch": 2.35,
                    "overtime_double_shift": 2.10,
                },
            ),
            generator_controls=ScenarioGeneratorControls(
                anomaly_dollar_multiplier=1.55,
                residual_target_multiplier=0.80,
            ),
            metadata={
                "scenario_family": ScenarioFamily.BASELINE,
                "status": "implemented",
                "display_name": "Heavy dollar tail",
                "what_changes": "fewer but larger financial losses",
                "description": "Residual anomalies are less frequent overall but more concentrated in higher-dollar payroll loss events.",
            },
        ),
        "subtle-residual-issues": ScenarioSpec(
            name="subtle-residual-issues",
            seed_offset=40,
            anomaly_plan=AnomalyPlan(
                target_count=125,
                category_weights={
                    str(SNFAnomalyCategory.PAID_VS_SCHEDULED_MISMATCH): 0.40,
                    str(SNFAnomalyCategory.DUPLICATE_PREMIUM): 0.20,
                    str(SNFAnomalyCategory.UNSUPPORTED_SHIFT_DIFFERENTIAL): 0.18,
                    str(SNFAnomalyCategory.CROSS_FACILITY_ALLOCATION): 0.10,
                    str(SNFAnomalyCategory.RETRO_RATE_MISMATCH): 0.07,
                    str(SNFAnomalyCategory.OVERTIME_DOUBLE_SHIFT): 0.05,
                },
                severity_multipliers={
                    "cross_facility_allocation": 0.80,
                    "retro_rate_mismatch": 0.65,
                    "overtime_double_shift": 0.60,
                },
            ),
            generator_controls=ScenarioGeneratorControls(
                anomaly_dollar_multiplier=0.72,
                residual_target_multiplier=0.88,
            ),
            metadata={
                "scenario_family": ScenarioFamily.BASELINE,
                "status": "implemented",
                "display_name": "Subtle residual issues",
                "what_changes": "hard rules catch more obvious issues; residual cases are lower-signal",
                "description": "The remaining residual queue is dominated by lower-dollar, lower-signal issues after more obvious severe cases are effectively removed upstream.",
            },
        ),
        "biased-historical-corrections": ScenarioSpec(
            name="biased-historical-corrections",
            seed_offset=50,
            generator_controls=ScenarioGeneratorControls(
                observed_review_bias_multiplier=1.65,
            ),
            metadata={
                "scenario_family": ScenarioFamily.BASELINE,
                "status": "implemented",
                "display_name": "Biased historical corrections",
                "what_changes": "observed corrections are more strongly selected by prior review logic",
                "description": "Historical observed-correction labels concentrate more heavily on high-dollar, manual-edit, and low-maturity records.",
            },
        ),
        "diversified-severe-issues": ScenarioSpec(
            name="diversified-severe-issues",
            seed_offset=60,
            anomaly_plan=AnomalyPlan(
                target_count=145,
                category_weights={
                    str(SNFAnomalyCategory.PAID_VS_SCHEDULED_MISMATCH): 0.18,
                    str(SNFAnomalyCategory.DUPLICATE_PREMIUM): 0.12,
                    str(SNFAnomalyCategory.UNSUPPORTED_SHIFT_DIFFERENTIAL): 0.18,
                    str(SNFAnomalyCategory.CROSS_FACILITY_ALLOCATION): 0.18,
                    str(SNFAnomalyCategory.RETRO_RATE_MISMATCH): 0.17,
                    str(SNFAnomalyCategory.OVERTIME_DOUBLE_SHIFT): 0.17,
                },
                severity_multipliers={
                    "unsupported_shift_differential": 1.15,
                    "cross_facility_allocation": 1.35,
                    "retro_rate_mismatch": 1.45,
                    "overtime_double_shift": 1.40,
                },
            ),
            generator_controls=ScenarioGeneratorControls(
                anomaly_dollar_multiplier=1.15,
            ),
            metadata={
                "scenario_family": ScenarioFamily.BASELINE,
                "status": "implemented",
                "display_name": "Diversified severe issues",
                "what_changes": "severe cases spread across multiple anomaly families",
                "description": "High-priority residual cases are distributed across several anomaly families instead of clustering in one dominant severe pattern.",
            },
        ),
        "temporal-payroll-drift": ScenarioSpec(
            name="temporal-payroll-drift",
            seed_offset=70,
            drift_plans=(
                DriftPlan(
                    name="late-period-overtime-drift",
                    start_period=22,
                    overtime_multiplier=1.20,
                ),
                DriftPlan(
                    name="late-period-payroll-inflation",
                    start_period=24,
                    gross_pay_multiplier=1.08,
                    deduction_multiplier=1.03,
                ),
            ),
            change_points=(
                ChangePointEvent(
                    name="late-period-rate-shift",
                    start_period=26,
                    field=PayrollCol.GROSS_PAY,
                    multiplier=1.05,
                ),
            ),
            generator_controls=ScenarioGeneratorControls(
                timekeeping_noise_multiplier=1.20,
            ),
            metadata={
                "scenario_family": ScenarioFamily.BASELINE,
                "status": "implemented",
                "display_name": "Temporal payroll drift",
                "what_changes": "pay rates, overtime norms, or timekeeping patterns shift over time",
                "description": "Later payroll cycles drift in overtime behavior, pay totals, and timekeeping noise relative to earlier periods.",
            },
        ),
    }


def diagnostic_scenario_catalog() -> dict[str, ScenarioSpec]:
    catalog = {
        **implemented_dgp_scenario_catalog(),
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
        "baseline": "baseline-operations",
        "overtime-staffing-pressure": "heavy-dollar-tail",
        "premium-mismatch": "high-timekeeping-noise",
        "rule-friendly": "high-timekeeping-noise",
        "statistical-friendly": "heavy-dollar-tail",
        "ml-friendly": "baseline-operations",
        "exposure-heavy": "heavy-dollar-tail",
        "subgroup-drift": "high-facility-heterogeneity",
        "calendar-drift": "temporal-payroll-drift",
        "queue-stress": "biased-historical-corrections",
    }
    for alias, target in legacy_aliases.items():
        base = catalog[target]
        catalog[alias] = ScenarioSpec(
            name=alias,
            seed_offset=base.seed_offset + len(alias),
            anomaly_plan=base.anomaly_plan,
            drift_plans=base.drift_plans,
            change_points=base.change_points,
            generator_controls=base.generator_controls,
            metadata={**base.metadata, "alias_for": target},
        )
    for scenario in catalog.values():
        scenario.metadata.setdefault("future_scenarios", FUTURE_SCENARIO_CATALOG)
    return catalog


def diagnostic_scenario_presets(
    names: tuple[str, ...] | None = None,
) -> dict[str, ScenarioSpec]:
    catalog = diagnostic_scenario_catalog()
    if names is None:
        return catalog
    return {name: catalog[name] for name in names}
