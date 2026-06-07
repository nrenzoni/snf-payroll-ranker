from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import TypeVar

import pytest

from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import generate_employee_pay_cycles
from payroll_anomaly_ranking.evaluation import (
    employee_cycle_feature_ablation,
    evaluate_employee_cycle_scores,
)
from payroll_anomaly_ranking.models import score_employee_pay_cycles
from payroll_anomaly_ranking.scenario_benchmark import (
    run_employee_cycle_scenario_benchmark,
)
from payroll_anomaly_ranking.scenarios import implemented_dgp_scenario_catalog

pytestmark = pytest.mark.integration

T = TypeVar("T")


@dataclass
class RecordingProgress:
    calls: list[tuple[str, int | None, int]] = field(default_factory=list)

    def iter(
        self,
        iterable: Iterable[T],
        *,
        desc: str,
        total: int | None = None,
        unit: str = "it",
    ) -> Iterator[T]:
        count = 0
        for item in iterable:
            count += 1
            yield item
        self.calls.append((desc, total, count))

    def descriptions(self) -> set[str]:
        return {desc for desc, _, _ in self.calls}


def test_progress_reporter_instruments_generation_scoring_and_evaluation() -> None:
    config = PayrollConfig(
        facility_count=3,
        employee_count=40,
        pay_periods=8,
        employee_cycle_review_budget_percents=(0.05,),
        ltr_num_threads=1,
    )
    progress = RecordingProgress()

    generated = generate_employee_pay_cycles(config, progress=progress)
    scored = score_employee_pay_cycles(
        generated.payroll,
        config,
        progress=progress,
    ).scored
    evaluation = evaluate_employee_cycle_scores(scored, config, progress=progress)
    feature_ablation = employee_cycle_feature_ablation(
        generated.payroll,
        config,
        progress=progress,
    )

    assert generated.payroll.height > 0
    assert scored.height > 0
    assert evaluation.model_comparison.height > 0
    assert feature_ablation.height > 0
    assert {
        "Generating payroll data",
        "Building employee cycles",
        "Scoring employee cycles",
        "Evaluating review budgets",
        "Comparing employee-cycle models",
        "Running rolling-origin evaluation",
        "Running feature ablation",
    } <= progress.descriptions()


def test_progress_reporter_instruments_scenario_benchmark_units() -> None:
    config = PayrollConfig(
        facility_count=3,
        employee_count=35,
        pay_periods=8,
        employee_cycle_review_budget_percents=(0.05,),
        ltr_num_threads=1,
    )
    scenarios = implemented_dgp_scenario_catalog()
    progress = RecordingProgress()

    benchmark = run_employee_cycle_scenario_benchmark(
        config,
        scenarios={"baseline-operations": scenarios["baseline-operations"]},
        seeds=(config.seed,),
        progress=progress,
    )

    assert benchmark.metric_units.height > 0
    assert ("Running scenario benchmark", 1, 1) in progress.calls
