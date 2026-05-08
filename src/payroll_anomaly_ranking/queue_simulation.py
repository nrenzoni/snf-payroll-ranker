from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

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
    thresholds = _threshold_specs(scored, spec)
    snapshots = _queue_snapshots(scored, periods, thresholds, spec)
    for iteration in range(1, spec.iterations + 1):
        for snapshot in snapshots:
            capacity = _capacity_for_period(spec, snapshot.period, rng)
            reviewed_records = min(capacity, snapshot.queue_size)
            captured_anomalies = snapshot.captured_anomalies(reviewed_records)
            dollars_captured = snapshot.dollars_captured(reviewed_records)
            missed_anomalies = snapshot.missed_anomalies(reviewed_records)
            missed_exposure = snapshot.missed_estimated_exposure(reviewed_records)
            missed_dollars = snapshot.missed_synthetic_anomaly_dollars(reviewed_records)
            # Queue membership is deterministic for a period-threshold policy; only
            # simulated capacity varies across Monte Carlo iterations.
            threshold = snapshot.threshold
            demand_mode = snapshot.demand_mode
            period = snapshot.period
            rows.append(
                {
                    "iteration": iteration,
                    "scenario": spec.scenario,
                    PayrollCol.PAY_PERIOD_INDEX: period,
                    "demand_mode": demand_mode,
                    "score_threshold": spec.score_threshold,
                    "resolved_threshold": threshold,
                    "adaptive_threshold_quantile": spec.adaptive_threshold_quantile,
                    "review_budget": spec.review_budget,
                    "capacity": capacity,
                    "queue_size": snapshot.queue_size,
                    "candidate_queue_size": snapshot.queue_size,
                    "reviewed_records": reviewed_records,
                    "overload": capacity < snapshot.queue_size,
                    "captured_anomalies": captured_anomalies,
                    "dollars_captured": dollars_captured,
                    "missed_anomalies": missed_anomalies,
                    "missed_estimated_exposure": missed_exposure,
                    "missed_synthetic_anomaly_dollars": missed_dollars,
                },
            )
    return pl.DataFrame(rows)


@dataclass(frozen=True)
class _QueueSnapshot:
    period: int
    demand_mode: str
    threshold: float | None
    queue_size: int
    anomaly_prefix: np.ndarray
    dollars_prefix: np.ndarray
    exposure_prefix: np.ndarray

    def captured_anomalies(self, reviewed_records: int) -> float:
        return float(self.anomaly_prefix[reviewed_records])

    def dollars_captured(self, reviewed_records: int) -> float:
        return float(self.dollars_prefix[reviewed_records])

    def missed_anomalies(self, reviewed_records: int) -> float:
        return float(self.anomaly_prefix[-1] - self.anomaly_prefix[reviewed_records])

    def missed_estimated_exposure(self, reviewed_records: int) -> float:
        return float(self.exposure_prefix[-1] - self.exposure_prefix[reviewed_records])

    def missed_synthetic_anomaly_dollars(self, reviewed_records: int) -> float:
        return float(self.dollars_prefix[-1] - self.dollars_prefix[reviewed_records])


def _queue_snapshots(
    scored: pl.DataFrame,
    periods: list[int],
    thresholds: list[tuple[str, float | None]],
    spec: QueueSimulationSpec,
) -> list[_QueueSnapshot]:
    snapshots: list[_QueueSnapshot] = []
    for period in periods:
        period_scores = scored.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) == period)
        ordered = period_scores.sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True)
        for demand_mode, threshold in thresholds:
            if threshold is None:
                queue = ordered.head(min(spec.review_budget, period_scores.height))
            else:
                queue = ordered.filter(
                    pl.col(ScoreCol.FINAL_ANOMALY_SCORE) >= threshold,
                )
            snapshots.append(
                _QueueSnapshot(
                    period=period,
                    demand_mode=demand_mode,
                    threshold=threshold,
                    queue_size=queue.height,
                    anomaly_prefix=_prefix_sum(queue, PayrollCol.IS_ANOMALY),
                    dollars_prefix=_prefix_sum(queue, PayrollCol.ANOMALY_DOLLARS),
                    exposure_prefix=_prefix_sum(queue, ScoreCol.ESTIMATED_EXPOSURE),
                ),
            )
    return snapshots


def summarize_queue_simulation(simulation: pl.DataFrame) -> pl.DataFrame:
    if simulation.is_empty():
        return pl.DataFrame()
    group_cols: list[str] = [PayrollCol.PAY_PERIOD_INDEX]
    for column in ["scenario", "demand_mode", "resolved_threshold"]:
        if column in simulation.columns:
            group_cols.insert(0, column)
    return simulation.group_by(group_cols).agg(
        pl.mean("queue_size").alias("avg_queue_size"),
        pl.mean("candidate_queue_size").alias("avg_candidate_queue_size"),
        pl.mean("reviewed_records").alias("avg_reviewed_records"),
        pl.mean("overload").alias("overload_probability"),
        pl.mean("captured_anomalies").alias("avg_captured_anomalies"),
        pl.mean("dollars_captured").alias("avg_dollars_captured"),
        pl.mean("missed_anomalies").alias("avg_missed_anomalies"),
        pl.mean("missed_estimated_exposure").alias("avg_missed_estimated_exposure"),
        pl.mean("missed_synthetic_anomaly_dollars").alias(
            "avg_missed_synthetic_anomaly_dollars",
        ),
        pl.first("review_budget").alias("review_budget"),
        pl.first("score_threshold").alias("score_threshold"),
        pl.first("adaptive_threshold_quantile").alias("adaptive_threshold_quantile"),
    )


def compare_scenarios(
    config: PayrollConfig,
    scenarios: Mapping[str, ScenarioSpec | None],
    queue_spec: QueueSimulationSpec = QueueSimulationSpec(),
) -> pl.DataFrame:
    rows = []
    for scenario_name, scenario in scenarios.items():
        results = run_pipeline(config, scenario=scenario)
        scenario_queue_spec = QueueSimulationSpec(
            iterations=queue_spec.iterations,
            review_budget=queue_spec.review_budget,
            score_threshold=queue_spec.score_threshold,
            score_thresholds=queue_spec.score_thresholds,
            adaptive_threshold_quantile=queue_spec.adaptive_threshold_quantile,
            fixed_capacity=queue_spec.fixed_capacity,
            period_capacity=queue_spec.period_capacity,
            period_capacity_multipliers=queue_spec.period_capacity_multipliers,
            capacity_sd=queue_spec.capacity_sd,
            seed=queue_spec.seed,
            scenario=scenario_name,
        )
        summary = summarize_queue_simulation(
            simulate_queue_capacity(results.scored, scenario_queue_spec),
        )
        for row in summary.to_dicts():
            rows.append({**row, "scenario": row.get("scenario", scenario_name)})
    return pl.DataFrame(rows, infer_schema_length=None)


def _capacity_for_period(
    spec: QueueSimulationSpec,
    period: int,
    rng: np.random.Generator,
) -> int:
    base = spec.period_capacity.get(period, spec.fixed_capacity or spec.review_budget)
    base = round(base * spec.period_capacity_multipliers.get(period, 1.0))
    if spec.capacity_sd <= 0:
        return max(base, 0)
    return max(round(rng.normal(base, spec.capacity_sd)), 0)


def _threshold_specs(
    scored: pl.DataFrame,
    spec: QueueSimulationSpec,
) -> list[tuple[str, float | None]]:
    if spec.score_thresholds:
        return [("threshold_grid", threshold) for threshold in spec.score_thresholds]
    if spec.adaptive_threshold_quantile is not None:
        quantile = min(max(spec.adaptive_threshold_quantile, 0.0), 1.0)
        threshold = scored.select(
            pl.col(ScoreCol.FINAL_ANOMALY_SCORE).quantile(quantile),
        ).item()
        return [("adaptive_threshold", float(threshold or 0.0))]
    if spec.score_threshold is not None:
        return [("score_threshold", spec.score_threshold)]
    return [("fixed_top_k", None)]


def _prefix_sum(frame: pl.DataFrame, column: str) -> np.ndarray:
    if frame.is_empty() or column not in frame.columns:
        return np.array([0.0])
    values = frame.get_column(column).to_numpy().astype(float)
    return np.concatenate(([0.0], np.cumsum(values)))
