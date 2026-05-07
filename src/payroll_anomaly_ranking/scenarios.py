from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class AnomalyPlan:
    category_weights: dict[str, float] = field(default_factory=dict)
    target_count: int | None = None
    severity_multipliers: dict[str, float] = field(default_factory=dict)


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
    fixed_capacity: int | None = None
    period_capacity: dict[int, int] = field(default_factory=dict)
    capacity_sd: float = 0.0
    seed: int = 42


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
