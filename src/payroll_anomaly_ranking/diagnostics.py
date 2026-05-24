from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace

import numpy as np
import polars as pl

from payroll_anomaly_ranking.columns import MetricCol, PayrollCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.evaluation import (
    dollars_captured_at_k,
    precision_recall_at_k,
    threshold_baseline_metrics,
)
from payroll_anomaly_ranking.scenarios import ScenarioSpec, diagnostic_scenario_presets

SCORE_SIGNALS = {
    "hybrid": ScoreCol.FINAL_ANOMALY_SCORE,
    "rule": ScoreCol.RULE_SCORE,
    "statistical": ScoreCol.STATISTICAL_SCORE,
    "ml": ScoreCol.ML_SCORE,
    "exposure": ScoreCol.EXPOSURE_SCORE,
}
BUSINESS_PROOF_METHODS = (
    ("rule", ScoreCol.RULE_SCORE, "deterministic rules"),
    ("statistical", ScoreCol.STATISTICAL_SCORE, "robust statistics"),
    ("ml", ScoreCol.ML_SCORE, "unsupervised ML"),
    ("hybrid", ScoreCol.FINAL_ANOMALY_SCORE, "hybrid ranking"),
)
BUSINESS_PROOF_MAIN_SCENARIOS = (
    "baseline",
    "overtime-staffing-pressure",
    "premium-mismatch",
)


def review_budget_interval_summary(
    scored: pl.DataFrame,
    k: int = 25,
    samples: int = 250,
    seed: int = 42,
) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(samples):
        sample = scored.sample(
            fraction=1.0,
            with_replacement=True,
            seed=int(rng.integers(1_000_000_000)),
        )
        metrics = {
            **precision_recall_at_k(sample, k),
            **dollars_captured_at_k(sample, k),
        }
        estimates.append(metrics)
    rows = []
    for metric in [
        "precision_at_k",
        "recall_at_k",
        "dollars_captured_at_k",
        "dollar_capture_rate",
    ]:
        values = np.array([row[metric] for row in estimates], dtype=float)
        rows.append(
            {
                "metric": metric,
                "k": k,
                "mean": float(values.mean()),
                "lower_95": float(np.quantile(values, 0.025)),
                "upper_95": float(np.quantile(values, 0.975)),
                "method": "bootstrap_posterior_simulation",
                "scope": "internal_evaluation_only",
            },
        )
    return pl.DataFrame(rows)


def component_superiority_summary(
    scored: pl.DataFrame,
    k: int = 25,
    samples: int = 100,
    seed: int = 42,
) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    wins: dict[tuple[str, str], int] = {}
    totals: dict[tuple[str, str], int] = {}
    names = list(SCORE_SIGNALS)
    for _ in range(samples):
        sample = scored.sample(
            fraction=1.0,
            with_replacement=True,
            seed=int(rng.integers(1_000_000_000)),
        )
        performance = {
            name: _precision_for_signal(sample, signal, k)
            for name, signal in SCORE_SIGNALS.items()
            if signal in sample.columns
        }
        for left in names:
            for right in names:
                if left == right or left not in performance or right not in performance:
                    continue
                key = (left, right)
                wins[key] = wins.get(key, 0) + int(
                    performance[left] > performance[right],
                )
                totals[key] = totals.get(key, 0) + 1
    rows = []
    for left, right in sorted(totals):
        probability = wins[(left, right)] / totals[(left, right)]
        rows.append(
            {
                "left_signal": left,
                "right_signal": right,
                "metric": f"precision_at_{k}",
                "scenario": "single_world_bootstrap",
                "scope": "single_world_bootstrap",
                "superiority_probability": probability,
                "win_probability": probability,
                "win_frequency": wins[(left, right)],
                "samples": totals[(left, right)],
                "mean_delta": None,
                "lower_95": None,
                "upper_95": None,
            },
        )
    return pl.DataFrame(rows)


def business_proof_ranking_units(
    config: PayrollConfig = PayrollConfig(),
    scenarios: Mapping[str, ScenarioSpec | None] | None = None,
    seeds: tuple[int, ...] = (42, 43),
    review_budgets: tuple[int, ...] | None = None,
) -> pl.DataFrame:
    from payroll_anomaly_ranking.pipeline import (
        PipelineIncludeConfig,
        run_shift_level_pipeline,
    )

    scenario_map = scenarios or diagnostic_scenario_presets(
        BUSINESS_PROOF_MAIN_SCENARIOS,
    )
    budgets = review_budgets or config.review_budgets
    rows: list[dict[str, object]] = []
    for scenario_name, scenario in scenario_map.items():
        for seed in seeds:
            seed_config = replace(config, seed=seed)
            scored = run_shift_level_pipeline(
                seed_config,
                scenario=scenario,
                include=PipelineIncludeConfig.scored_only(),
            ).scored
            for budget in budgets:
                unit = f"{scenario_name}|seed={seed}|budget={budget}"
                for method, score_col, method_type in BUSINESS_PROOF_METHODS:
                    rows.append(
                        {
                            "scenario": scenario_name,
                            "seed": seed,
                            "unit": unit,
                            "method": method,
                            "method_type": method_type,
                            **_facility_budget_metrics(scored, score_col, budget),
                        },
                    )
    return pl.DataFrame(rows, infer_schema_length=None)


def business_proof_threshold_units(
    config: PayrollConfig = PayrollConfig(),
    scenarios: Mapping[str, ScenarioSpec | None] | None = None,
    seeds: tuple[int, ...] = (42, 43),
) -> pl.DataFrame:
    from payroll_anomaly_ranking.pipeline import (
        PipelineIncludeConfig,
        run_shift_level_pipeline,
    )

    scenario_map = scenarios or diagnostic_scenario_presets(
        BUSINESS_PROOF_MAIN_SCENARIOS,
    )
    rows: list[dict[str, object]] = []
    for scenario_name, scenario in scenario_map.items():
        for seed in seeds:
            seed_config = replace(config, seed=seed)
            scored = run_shift_level_pipeline(
                seed_config,
                scenario=scenario,
                include=PipelineIncludeConfig.scored_only(),
            ).scored
            thresholds = threshold_baseline_metrics(scored, seed_config).with_columns(
                pl.lit(scenario_name).alias("scenario"),
                pl.lit(seed).alias("seed"),
                pl.concat_str(
                    [
                        pl.lit(scenario_name),
                        pl.lit("|seed="),
                        pl.lit(str(seed)),
                    ],
                ).alias("unit"),
                pl.col("baseline").alias("method"),
                pl.lit("manual threshold").alias("method_type"),
            )
            rows.extend(thresholds.to_dicts())
    return pl.DataFrame(rows, infer_schema_length=None)


def business_proof_metric_intervals(
    units: pl.DataFrame,
    metric_columns: tuple[str, ...],
    group_columns: tuple[str, ...],
) -> pl.DataFrame:
    if units.is_empty():
        return pl.DataFrame()
    long = units.unpivot(
        index=list(group_columns),
        on=[column for column in metric_columns if column in units.columns],
        variable_name="metric",
        value_name="value",
    )
    return long.group_by([*group_columns, "metric"]).agg(
        pl.mean("value").alias("mean"),
        pl.col("value").quantile(0.025).alias("lower_95"),
        pl.col("value").quantile(0.975).alias("upper_95"),
        pl.len().alias("samples"),
    )


def business_proof_hybrid_win_rates(
    ranking_units: pl.DataFrame,
    metric: str = MetricCol.EXPOSURE_PER_REVIEW,
) -> pl.DataFrame:
    if ranking_units.is_empty() or metric not in ranking_units.columns:
        return pl.DataFrame()
    rows: list[dict[str, object]] = []
    comparators = sorted(
        method
        for method in ranking_units.get_column("method").unique().to_list()
        if method != "hybrid"
    )
    scenarios = ranking_units.get_column("scenario").unique().to_list()
    budgets = sorted(ranking_units.get_column(MetricCol.K).unique().to_list())
    for scenario in scenarios:
        for budget in budgets:
            frame = ranking_units.filter(
                (pl.col("scenario") == scenario) & (pl.col(MetricCol.K) == budget),
            )
            for comparator in comparators:
                deltas = []
                for unit in frame.get_column("unit").unique().to_list():
                    unit_rows = frame.filter(pl.col("unit") == unit)
                    hybrid_rows = unit_rows.filter(pl.col("method") == "hybrid")
                    comparator_rows = unit_rows.filter(pl.col("method") == comparator)
                    if hybrid_rows.is_empty() or comparator_rows.is_empty():
                        continue
                    deltas.append(
                        float(hybrid_rows.select(metric).item())
                        - float(comparator_rows.select(metric).item()),
                    )
                if not deltas:
                    continue
                values = np.array(deltas, dtype=float)
                rows.append(
                    {
                        "scenario": scenario,
                        MetricCol.K: float(budget),
                        "comparator": comparator,
                        "metric": metric,
                        "win_probability": float((values > 0).mean()),
                        "mean_delta": float(values.mean()),
                        "lower_95": float(np.quantile(values, 0.025)),
                        "upper_95": float(np.quantile(values, 0.975)),
                        "samples": len(values),
                    },
                )
    return pl.DataFrame(rows, infer_schema_length=None)


def run_diagnostic_comparison_units(
    config: PayrollConfig = PayrollConfig(),
    scenarios: Mapping[str, ScenarioSpec | None] | None = None,
    seeds: tuple[int, ...] = (42, 43),
    origins: tuple[str, ...] = ("default",),
    k: int | None = None,
) -> pl.DataFrame:
    from payroll_anomaly_ranking.pipeline import (
        PipelineIncludeConfig,
        run_shift_level_pipeline,
    )

    scenario_map = scenarios or diagnostic_scenario_presets(
        (
            "baseline",
            "rule-friendly",
            "statistical-friendly",
            "ml-friendly",
            "exposure-heavy",
            "subgroup-drift",
            "calendar-drift",
            "queue-stress",
        ),
    )
    budget = k or config.review_budgets[0]
    rows: list[dict[str, object]] = []
    for scenario_name, scenario in scenario_map.items():
        for seed in seeds:
            seed_config = replace(config, seed=seed)
            results = run_shift_level_pipeline(
                seed_config,
                scenario=scenario,
                include=PipelineIncludeConfig.scored_only(),
            )
            scored = results.scored
            for origin in origins:
                unit = f"{scenario_name}|seed={seed}|origin={origin}"
                for signal_name, signal_column in SCORE_SIGNALS.items():
                    if signal_column not in scored.columns:
                        continue
                    metrics = _metrics_for_signal(scored, signal_column, budget)
                    rows.append(
                        {
                            "scenario": scenario_name,
                            "seed": seed,
                            "origin": origin,
                            "unit": unit,
                            "signal": signal_name,
                            **metrics,
                        },
                    )
    return pl.DataFrame(rows, infer_schema_length=None)


def pairwise_component_superiority(
    unit_metrics: pl.DataFrame,
    metric: str = "precision_at_k",
    by_scenario: bool = True,
) -> pl.DataFrame:
    if unit_metrics.is_empty() or metric not in unit_metrics.columns:
        return pl.DataFrame()
    scopes: list[tuple[str, pl.DataFrame]] = [("aggregate", unit_metrics)]
    if by_scenario and "scenario" in unit_metrics.columns:
        scopes.extend(
            (str(scenario), unit_metrics.filter(pl.col("scenario") == scenario))
            for scenario in unit_metrics.get_column("scenario").unique().to_list()
        )
    rows: list[dict[str, object]] = []
    signals = sorted(unit_metrics.get_column("signal").unique().to_list())
    for scope, frame in scopes:
        for left in signals:
            for right in signals:
                if left == right:
                    continue
                deltas = []
                for unit in frame.get_column("unit").unique().to_list():
                    unit_rows = frame.filter(pl.col("unit") == unit)
                    left_rows = unit_rows.filter(pl.col("signal") == left)
                    right_rows = unit_rows.filter(pl.col("signal") == right)
                    if left_rows.is_empty() or right_rows.is_empty():
                        continue
                    deltas.append(
                        float(left_rows.select(metric).item())
                        - float(right_rows.select(metric).item()),
                    )
                if not deltas:
                    continue
                values = np.array(deltas, dtype=float)
                wins = int((values > 0).sum())
                rows.append(
                    {
                        "left_signal": left,
                        "right_signal": right,
                        "metric": metric,
                        "scenario": scope,
                        "scope": scope,
                        "superiority_probability": wins / len(values),
                        "win_probability": wins / len(values),
                        "win_frequency": wins,
                        "samples": len(values),
                        "mean_delta": float(values.mean()),
                        "lower_95": float(np.quantile(values, 0.025)),
                        "upper_95": float(np.quantile(values, 0.975)),
                    },
                )
    return pl.DataFrame(rows, infer_schema_length=None)


def subgroup_diagnostics(
    scored: pl.DataFrame,
    dimensions: tuple[str, ...] = (
        PayrollCol.FACILITY_ID,
        PayrollCol.UNIT,
        PayrollCol.ROLE,
        PayrollCol.LICENSE_TYPE,
        PayrollCol.SHIFT_TYPE,
        PayrollCol.PAY_CODE_CATEGORY,
        PayrollCol.APPROVAL_STATUS,
    ),
    k: int = 25,
    scenario: str = "default",
) -> pl.DataFrame:
    rows = []
    global_rate = scored.select(pl.mean(PayrollCol.IS_ANOMALY)).item() or 0.0
    prior_strength = 25.0
    reviewed = scored.with_columns(
        (pl.col(ScoreCol.PAY_PERIOD_RANK) <= k).alias("reviewed"),
    )
    for dimension in dimensions:
        if dimension not in reviewed.columns:
            continue
        grouped = reviewed.group_by(dimension).agg(
            pl.len().alias("records"),
            pl.sum(PayrollCol.IS_ANOMALY).alias("true_anomalies"),
            pl.sum("reviewed").alias("reviewed_records"),
            ((pl.col("reviewed")) & (pl.col(PayrollCol.IS_ANOMALY) == 1))
            .sum()
            .alias("true_positive_reviews"),
            ((~pl.col("reviewed")) & (pl.col(PayrollCol.IS_ANOMALY) == 1))
            .sum()
            .alias("false_negatives"),
            ((pl.col("reviewed")) & (pl.col(PayrollCol.IS_ANOMALY) == 0))
            .sum()
            .alias("false_positives"),
        )
        for row in grouped.to_dicts():
            records = max(float(row["records"]), 1.0)
            raw_rate = float(row["true_anomalies"]) / records
            pooled = (float(row["true_anomalies"]) + global_rate * prior_strength) / (
                records + prior_strength
            )
            rows.append(
                {
                    "dimension": dimension,
                    "subgroup": str(row[dimension]),
                    "scenario": scenario,
                    **{key: row[key] for key in row if key != dimension},
                    "anomaly_count": row["true_anomalies"],
                    "raw_anomaly_rate": raw_rate,
                    "pooled_anomaly_rate": pooled,
                    "shrinkage": pooled - raw_rate,
                    "lower_95": max(
                        0.0,
                        pooled
                        - 1.96 * np.sqrt(max(pooled * (1 - pooled), 0.0) / records),
                    ),
                    "upper_95": min(
                        1.0,
                        pooled
                        + 1.96 * np.sqrt(max(pooled * (1 - pooled), 0.0) / records),
                    ),
                },
            )
    return pl.DataFrame(rows, infer_schema_length=None)


def top_subgroup_diagnostics(
    subgroups: pl.DataFrame,
    top_n: int = 12,
    sort_by: str = "anomaly_count",
) -> pl.DataFrame:
    if subgroups.is_empty():
        return pl.DataFrame()
    order_column = sort_by if sort_by in subgroups.columns else "records"
    return (
        subgroups.with_columns(
            (pl.col("raw_anomaly_rate") - pl.col("pooled_anomaly_rate")).alias(
                "raw_pooled_delta",
            ),
        )
        .sort(["scenario", order_column], descending=[False, True])
        .group_by("scenario", maintain_order=True)
        .head(top_n)
    )


def expected_pay_calibration(
    scored: pl.DataFrame,
    by: str | None = None,
    scenario: str = "default",
) -> pl.DataFrame:
    required = {
        ScoreCol.EXPECTED_GROSS_PAY_P10,
        ScoreCol.EXPECTED_GROSS_PAY_P50,
        ScoreCol.EXPECTED_GROSS_PAY_P90,
    }
    if not required <= set(scored.columns):
        return pl.DataFrame()
    frame = scored.with_columns(
        (
            (pl.col(PayrollCol.GROSS_PAY) >= pl.col(ScoreCol.EXPECTED_GROSS_PAY_P10))
            & (pl.col(PayrollCol.GROSS_PAY) <= pl.col(ScoreCol.EXPECTED_GROSS_PAY_P90))
        ).alias("covered"),
        (
            pl.col(ScoreCol.EXPECTED_GROSS_PAY_P90)
            - pl.col(ScoreCol.EXPECTED_GROSS_PAY_P10)
        ).alias("interval_width"),
        (pl.col(PayrollCol.GROSS_PAY) - pl.col(ScoreCol.EXPECTED_GROSS_PAY_P90))
        .clip(0, None)
        .alias("excess_over_p90"),
        (pl.col(PayrollCol.GROSS_PAY) - pl.col(ScoreCol.EXPECTED_GROSS_PAY_P50)).alias(
            "residual",
        ),
    )
    group_cols = [by] if by and by in frame.columns else []
    result = frame.group_by(group_cols).agg(
        pl.len().alias("records"),
        pl.mean("covered").alias("coverage"),
        pl.mean("interval_width").alias("avg_interval_width"),
        pl.mean("excess_over_p90").alias("avg_excess_over_p90"),
        pl.mean("residual").alias("avg_residual"),
    )
    if by and by in frame.columns:
        result = result.rename({by: "subgroup"}).with_columns(
            pl.lit(by).alias("subgroup_dimension"),
        )
    else:
        result = result.with_columns(
            pl.lit("all").alias("subgroup"),
            pl.lit("all").alias("subgroup_dimension"),
        )
    return result.with_columns(
        pl.lit(scenario).alias("scenario"),
        pl.col("avg_interval_width").alias("interval_width"),
        pl.col("avg_excess_over_p90").alias("excess_over_p90"),
        pl.col("avg_residual").alias("residual"),
    )


def calibration_plot_inputs(
    scored: pl.DataFrame,
    scenario: str = "default",
    by: str = PayrollCol.FACILITY_ID,
) -> pl.DataFrame:
    calibration = expected_pay_calibration(scored, by=by, scenario=scenario)
    if calibration.is_empty():
        return calibration
    return calibration.with_columns(
        pl.col("avg_interval_width").alias("interval_width"),
        pl.col("avg_residual").alias("residual"),
        pl.col("avg_excess_over_p90").alias("tail_excess"),
    )


def robustness_summary(frames: dict[str, pl.DataFrame], k: int = 25) -> pl.DataFrame:
    rows = []
    queues: dict[str, set[int]] = {}
    for name, scored in frames.items():
        metrics = precision_recall_at_k(scored, k)
        queue = set(
            scored.sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True)
            .head(k)
            .get_column(PayrollCol.RECORD_ID)
            .to_list(),
        )
        queues[name] = queue
        scenario, seed, origin = _parse_setting_name(name)
        rows.append(
            {
                "setting": name,
                "scenario": scenario,
                "seed": seed,
                "origin": origin,
                **metrics,
                "mean_performance": metrics["precision_at_k"],
                "performance_variability": 0.0,
                "queue_size": len(queue),
            },
        )
    for row in rows:
        overlaps = [
            _jaccard(queues[str(row["setting"])], other)
            for name, other in queues.items()
            if name != row["setting"]
        ]
        row["mean_queue_overlap"] = sum(overlaps) / len(overlaps) if overlaps else 1.0
        row["queue_overlap"] = row["mean_queue_overlap"]
        row["performance_instability"] = 1.0 - row["mean_queue_overlap"]
    result = pl.DataFrame(rows)
    if result.is_empty():
        return result
    return result.with_columns(
        (1.0 - pl.col("mean_queue_overlap")).alias("instability_metric"),
        pl.col("mean_queue_overlap").alias("queue_overlap"),
    )


def perturbation_sensitivity(
    scored: pl.DataFrame,
    perturb: Callable[[pl.DataFrame], pl.DataFrame],
    scorer: Callable[[pl.DataFrame], pl.DataFrame],
    threshold: float = 0.65,
) -> pl.DataFrame:
    baseline = scored.select(
        PayrollCol.RECORD_ID,
        ScoreCol.FINAL_ANOMALY_SCORE,
        ScoreCol.PAY_PERIOD_RANK,
    )
    perturbed = scorer(perturb(scored)).select(
        PayrollCol.RECORD_ID,
        pl.col(ScoreCol.FINAL_ANOMALY_SCORE).alias("perturbed_score"),
        pl.col(ScoreCol.PAY_PERIOD_RANK).alias("perturbed_rank"),
    )
    return baseline.join(perturbed, on=PayrollCol.RECORD_ID).with_columns(
        (pl.col("perturbed_score") - pl.col(ScoreCol.FINAL_ANOMALY_SCORE)).alias(
            "score_movement",
        ),
        (pl.col("perturbed_rank") - pl.col(ScoreCol.PAY_PERIOD_RANK)).alias(
            "rank_movement",
        ),
        (
            (pl.col(ScoreCol.FINAL_ANOMALY_SCORE) < threshold)
            & (pl.col("perturbed_score") >= threshold)
        ).alias("crossed_threshold"),
    )


def exposure_calibration(scored: pl.DataFrame) -> pl.DataFrame:
    if ScoreCol.ESTIMATED_EXPOSURE not in scored.columns:
        return pl.DataFrame()
    return (
        scored.group_by(PayrollCol.ANOMALY_CATEGORY)
        .agg(
            pl.len().alias("records"),
            pl.mean(ScoreCol.ESTIMATED_EXPOSURE).alias("avg_estimated_exposure"),
            pl.mean(PayrollCol.ANOMALY_DOLLARS).alias("avg_synthetic_anomaly_dollars"),
            pl.sum(ScoreCol.ESTIMATED_EXPOSURE).alias("total_estimated_exposure"),
            pl.sum(PayrollCol.ANOMALY_DOLLARS).alias("total_synthetic_anomaly_dollars"),
        )
        .with_columns(
            (
                pl.col("total_estimated_exposure")
                / (pl.col("total_synthetic_anomaly_dollars") + 1e-9)
            ).alias("exposure_to_synthetic_ratio"),
        )
    )


def _precision_for_signal(scored: pl.DataFrame, signal: str, k: int) -> float:
    ranked = (
        scored.sort([PayrollCol.PAY_PERIOD_INDEX, signal], descending=[False, True])
        .group_by(PayrollCol.PAY_PERIOD_INDEX)
        .head(k)
    )
    return ranked.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height / max(
        ranked.height,
        1,
    )


def _metrics_for_signal(scored: pl.DataFrame, signal: str, k: int) -> dict[str, float]:
    ranked = scored.with_columns(
        pl.col(signal).alias(ScoreCol.FINAL_ANOMALY_SCORE),
    ).with_columns(
        pl.col(ScoreCol.FINAL_ANOMALY_SCORE)
        .rank("ordinal", descending=True)
        .over(PayrollCol.PAY_PERIOD_INDEX)
        .alias(ScoreCol.PAY_PERIOD_RANK),
    )
    return {
        **precision_recall_at_k(ranked, k),
        **dollars_captured_at_k(ranked, k),
    }


def _facility_budget_metrics(
    scored: pl.DataFrame,
    signal: str,
    budget: int,
) -> dict[str, float]:
    ranked = scored.with_columns(
        pl.col(signal)
        .rank("ordinal", descending=True)
        .over([PayrollCol.PAY_PERIOD_INDEX, PayrollCol.FACILITY_ID])
        .alias("_method_rank"),
    )
    reviewed = ranked.filter(pl.col("_method_rank") <= budget)
    missed = ranked.filter(
        (pl.col("_method_rank") > budget) & (pl.col(PayrollCol.IS_ANOMALY) == 1),
    )
    true_positives = reviewed.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    total_anomalies = ranked.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height
    total_dollars = float(
        ranked.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
        .item()
        or 0.0,
    )
    captured_dollars = float(
        reviewed.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .select(pl.sum(PayrollCol.ANOMALY_DOLLARS))
        .item()
        or 0.0,
    )
    exposure = float(reviewed.select(pl.sum(ScoreCol.ESTIMATED_EXPOSURE)).item() or 0.0)
    return {
        MetricCol.K: float(budget),
        MetricCol.REVIEW_VOLUME: reviewed.height,
        MetricCol.NATIVE_REVIEW_BURDEN: reviewed.height,
        MetricCol.PRECISION_AT_K: true_positives / max(reviewed.height, 1),
        MetricCol.RECALL_AT_K: true_positives / max(total_anomalies, 1),
        MetricCol.EXPOSURE_CAPTURED_AT_K: exposure,
        MetricCol.EXPOSURE_PER_REVIEW: exposure / max(reviewed.height, 1),
        MetricCol.DOLLARS_CAPTURED_AT_K: captured_dollars,
        MetricCol.DOLLAR_CAPTURE_RATE: captured_dollars / total_dollars
        if total_dollars
        else 0.0,
        MetricCol.MISSED_ESTIMATED_EXPOSURE: float(
            missed.select(pl.sum(ScoreCol.ESTIMATED_EXPOSURE)).item() or 0.0,
        ),
    }


def _parse_setting_name(name: str) -> tuple[str, int | None, str]:
    parts = name.split("|")
    scenario = parts[0]
    seed = None
    origin = "default"
    for part in parts[1:]:
        if part.startswith("seed="):
            seed = int(part.removeprefix("seed="))
        elif part.startswith("origin="):
            origin = part.removeprefix("origin=")
    return scenario, seed, origin


def _jaccard(left: set[int], right: set[int]) -> float:
    return len(left & right) / max(len(left | right), 1)
