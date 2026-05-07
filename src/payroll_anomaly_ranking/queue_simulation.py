from __future__ import annotations

import numpy as np
import polars as pl

from payroll_anomaly_ranking.columns import PayrollCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import run_pipeline
from payroll_anomaly_ranking.scenarios import QueueSimulationSpec, ScenarioSpec


def simulate_queue_capacity(
    scored: pl.DataFrame,
    spec: QueueSimulationSpec = QueueSimulationSpec(),
) -> pl.DataFrame:
    rng = np.random.default_rng(spec.seed)
    periods = sorted(scored.get_column(PayrollCol.PAY_PERIOD_INDEX).unique().to_list())
    rows: list[dict[str, object]] = []
    for iteration in range(1, spec.iterations + 1):
        for period in periods:
            period_scores = scored.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) == period)
            queue = period_scores.sort(
                ScoreCol.FINAL_ANOMALY_SCORE,
                descending=True,
            ).head(
                min(spec.review_budget, period_scores.height),
            )
            capacity = _capacity_for_period(spec, period, rng)
            reviewed = queue.head(min(capacity, queue.height))
            missed = queue.slice(reviewed.height)
            rows.append(
                {
                    "iteration": iteration,
                    PayrollCol.PAY_PERIOD_INDEX: period,
                    "review_budget": spec.review_budget,
                    "capacity": capacity,
                    "queue_size": queue.height,
                    "reviewed_records": reviewed.height,
                    "overload": capacity < queue.height,
                    "captured_anomalies": _sum(reviewed, PayrollCol.IS_ANOMALY),
                    "dollars_captured": _sum(reviewed, PayrollCol.ANOMALY_DOLLARS),
                    "missed_anomalies": _sum(missed, PayrollCol.IS_ANOMALY),
                    "missed_estimated_exposure": _sum(
                        missed,
                        ScoreCol.ESTIMATED_EXPOSURE,
                    ),
                    "missed_synthetic_anomaly_dollars": _sum(
                        missed,
                        PayrollCol.ANOMALY_DOLLARS,
                    ),
                },
            )
    return pl.DataFrame(rows)


def summarize_queue_simulation(simulation: pl.DataFrame) -> pl.DataFrame:
    if simulation.is_empty():
        return pl.DataFrame()
    return simulation.group_by(PayrollCol.PAY_PERIOD_INDEX).agg(
        pl.mean("queue_size").alias("avg_queue_size"),
        pl.mean("reviewed_records").alias("avg_reviewed_records"),
        pl.mean("overload").alias("overload_probability"),
        pl.mean("captured_anomalies").alias("avg_captured_anomalies"),
        pl.mean("dollars_captured").alias("avg_dollars_captured"),
        pl.mean("missed_anomalies").alias("avg_missed_anomalies"),
        pl.mean("missed_estimated_exposure").alias("avg_missed_estimated_exposure"),
        pl.mean("missed_synthetic_anomaly_dollars").alias(
            "avg_missed_synthetic_anomaly_dollars",
        ),
    )


def compare_scenarios(
    config: PayrollConfig,
    scenarios: dict[str, ScenarioSpec | None],
    queue_spec: QueueSimulationSpec = QueueSimulationSpec(),
) -> pl.DataFrame:
    rows = []
    for scenario_name, scenario in scenarios.items():
        results = run_pipeline(config, scenario=scenario)
        summary = summarize_queue_simulation(
            simulate_queue_capacity(results["scored"], queue_spec),
        )
        for row in summary.to_dicts():
            rows.append({"scenario": scenario_name, **row})
    return pl.DataFrame(rows, infer_schema_length=None)


def _capacity_for_period(
    spec: QueueSimulationSpec,
    period: int,
    rng: np.random.Generator,
) -> int:
    base = spec.period_capacity.get(period, spec.fixed_capacity or spec.review_budget)
    if spec.capacity_sd <= 0:
        return max(int(base), 0)
    return max(int(round(rng.normal(base, spec.capacity_sd))), 0)


def _sum(frame: pl.DataFrame, column: str) -> float:
    if frame.is_empty() or column not in frame.columns:
        return 0.0
    return float(frame.select(pl.sum(column)).item() or 0.0)
