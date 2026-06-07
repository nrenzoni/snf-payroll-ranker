from __future__ import annotations

from dataclasses import dataclass, replace

import polars as pl

from payroll_anomaly_ranking.columns import MetricCol, PayrollCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import generate_employee_pay_cycles
from payroll_anomaly_ranking.evaluation import employee_cycle_grouped_metrics
from payroll_anomaly_ranking.models import (
    score_employee_pay_cycles_holdout,
    temporal_split,
)
from payroll_anomaly_ranking.progress import ProgressReporter, progress_or_none
from payroll_anomaly_ranking.scenarios import (
    ScenarioSpec,
    implemented_dgp_scenario_catalog,
)

SCENARIO_BENCHMARK_MODELS: tuple[tuple[str, ScoreCol], ...] = (
    ("classifier", ScoreCol.CLASSIFICATION_SCORE),
    ("cost_sensitive_classifier", ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE),
    ("regressor", ScoreCol.REGRESSION_SCORE),
    ("expected_value", ScoreCol.EXPECTED_VALUE_SCORE),
    ("learning_to_rank", ScoreCol.RANKING_SCORE),
    ("final_active_ranking", ScoreCol.FINAL_ANOMALY_SCORE),
)

SCENARIO_BENCHMARK_OBJECTIVES: tuple[tuple[str, str], ...] = (
    ("severity_ordering", str(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K)),
    ("dollar_recovery", str(MetricCol.DOLLARS_CAPTURED_AT_K)),
    ("incremental_utility", str(MetricCol.INCREMENTAL_UTILITY_AT_K)),
    ("queue_quality", str(MetricCol.RESIDUAL_NDCG_AT_K)),
)

SCENARIO_BENCHMARK_METRICS: tuple[str, ...] = (
    str(MetricCol.RESIDUAL_NDCG_AT_K),
    str(MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K),
    str(MetricCol.DOLLARS_CAPTURED_AT_K),
    str(MetricCol.REVIEWER_YIELD_AT_K),
    str(MetricCol.INCREMENTAL_UTILITY_AT_K),
    str(MetricCol.PR_AUC),
)


@dataclass(frozen=True)
class ScenarioBenchmarkResults:
    scenario_catalog: pl.DataFrame
    scenario_seed_design: pl.DataFrame
    scenario_summary: pl.DataFrame
    metric_units: pl.DataFrame
    winner_frequency: pl.DataFrame
    median_metric_summary: pl.DataFrame
    winner_map: pl.DataFrame


def run_employee_cycle_scenario_benchmark(
    config: PayrollConfig,
    *,
    scenarios: dict[str, ScenarioSpec] | None = None,
    seeds: tuple[int, ...] = (42,),
    progress: ProgressReporter | None = None,
) -> ScenarioBenchmarkResults:
    progress = progress_or_none(progress)
    scenario_catalog = scenarios or implemented_dgp_scenario_catalog()
    review_budgets = config.employee_cycle_review_budget_percents or tuple(
        float(budget) for budget in config.review_budgets
    )
    scenario_catalog_rows: list[dict[str, object]] = []
    scenario_seed_rows: list[dict[str, object]] = []
    scenario_summary_rows: list[dict[str, object]] = []
    metric_unit_rows: list[dict[str, object]] = []

    for scenario_name, scenario in scenario_catalog.items():
        scenario_catalog_rows.append(
            {
                "scenario": scenario_name,
                "display_name": str(
                    scenario.metadata.get("display_name", scenario.name),
                ),
                "what_changes": str(scenario.metadata.get("what_changes", "")),
                "status": str(scenario.metadata.get("status", "unknown")),
                "description": str(scenario.metadata.get("description", "")),
            },
        )
    scenario_seed_pairs = [
        (scenario_name, scenario, seed)
        for scenario_name, scenario in scenario_catalog.items()
        for seed in seeds
    ]
    for scenario_name, scenario, seed in progress.iter(
        scenario_seed_pairs,
        desc="Running scenario benchmark",
        total=len(scenario_seed_pairs),
        unit="unit",
    ):
        seed_config = replace(config, seed=seed)
        generated = generate_employee_pay_cycles(
            seed_config,
            scenario=scenario,
            progress=progress,
        )
        scoring_results = score_employee_pay_cycles_holdout(
            generated.payroll,
            seed_config,
            progress=progress,
        )
        scored = scoring_results.scored
        split = temporal_split(generated.payroll)
        scenario_seed_rows.append(
            {
                "scenario": scenario_name,
                "display_name": str(
                    scenario.metadata.get("display_name", scenario.name),
                ),
                "seed": seed,
                "unit": _benchmark_unit_name(scenario_name, seed),
                "review_budgets": ", ".join(
                    _format_review_budget_pct(budget) for budget in review_budgets
                ),
                "train_records": split.train.height + split.validation.height,
                "test_records": split.test.height,
                "test_periods": ", ".join(
                    str(period)
                    for period in sorted(
                        split.test.get_column(PayrollCol.PAY_PERIOD_INDEX)
                        .unique()
                        .to_list(),
                    )
                ),
                "test_residual_records": split.test.filter(
                    pl.col(PayrollCol.RESIDUAL_RECORD) == 1,
                ).height,
            },
        )
        scenario_summary_rows.append(
            _scenario_summary_row(
                scenario_name,
                scenario,
                seed,
                generated.payroll,
            ),
        )
        for model_name, score_col in SCENARIO_BENCHMARK_MODELS:
            scored_for_model = scored.with_columns(
                pl.col(score_col).alias(ScoreCol.FINAL_ANOMALY_SCORE),
            )
            for budget in review_budgets:
                metrics = employee_cycle_grouped_metrics(scored_for_model, budget)
                metric_unit_rows.extend(
                    _metric_unit_rows(
                        scenario_name,
                        scenario,
                        seed,
                        model_name,
                        budget,
                        metrics,
                    ),
                )

    metric_units = pl.DataFrame(metric_unit_rows, infer_schema_length=None)
    return ScenarioBenchmarkResults(
        scenario_catalog=pl.DataFrame(scenario_catalog_rows, infer_schema_length=None),
        scenario_seed_design=pl.DataFrame(scenario_seed_rows, infer_schema_length=None),
        scenario_summary=pl.DataFrame(scenario_summary_rows, infer_schema_length=None),
        metric_units=metric_units,
        winner_frequency=_winner_frequency(metric_units),
        median_metric_summary=_median_metric_summary(metric_units),
        winner_map=_winner_map(metric_units),
    )


def _benchmark_unit_name(scenario_name: str, seed: int) -> str:
    return f"{scenario_name}|seed={seed}"


def _format_review_budget_pct(budget: float) -> str:
    return f"{budget:.0%}" if budget <= 1 else str(int(budget))


def _scenario_summary_row(
    scenario_name: str,
    scenario: ScenarioSpec,
    seed: int,
    payroll: pl.DataFrame,
) -> dict[str, object]:
    residual = payroll.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)
    positive_residual = residual.filter(pl.col(PayrollCol.Y_ISSUE) == 1)
    dominant_issue_family = "none"
    if positive_residual.height:
        dominant_issue_family = str(
            positive_residual.group_by(PayrollCol.ANOMALY_CATEGORY)
            .agg(pl.len().alias("records"))
            .sort(["records", PayrollCol.ANOMALY_CATEGORY], descending=[True, False])
            .head(1)
            .select(PayrollCol.ANOMALY_CATEGORY)
            .item(),
        )
    label_bias_strength = _label_bias_strength(residual)
    return {
        "scenario": scenario_name,
        "display_name": str(scenario.metadata.get("display_name", scenario.name)),
        "seed": seed,
        "residual_issue_rate": round(
            float(residual.select(pl.mean(PayrollCol.Y_ISSUE)).item() or 0.0),
            4,
        ),
        "severe_issue_rate": round(
            float(
                residual.select(pl.mean(PayrollCol.RULE_MISSED_SEVERE_ISSUE)).item()
                or 0.0,
            ),
            4,
        ),
        "residual_dollars": round(
            float(residual.select(pl.sum(PayrollCol.Y_DOLLAR)).item() or 0.0),
            2,
        ),
        "dominant_issue_family": dominant_issue_family,
        "label_bias_strength": label_bias_strength,
    }


def _label_bias_strength(residual: pl.DataFrame) -> float:
    positive_residual = residual.filter(pl.col(PayrollCol.Y_ISSUE) == 1)
    if positive_residual.height < 2:
        return 0.0
    high_signal_threshold = float(
        positive_residual.select(pl.col(PayrollCol.Y_DOLLAR).quantile(0.75)).item()
        or 0.0,
    )
    high_signal = positive_residual.filter(
        (pl.col(PayrollCol.Y_DOLLAR) >= high_signal_threshold)
        | (pl.col(PayrollCol.PAYROLL_MATURITY) == "low"),
    )
    low_signal = positive_residual.filter(
        (pl.col(PayrollCol.Y_DOLLAR) < high_signal_threshold)
        & (pl.col(PayrollCol.PAYROLL_MATURITY) != "low"),
    )
    if high_signal.is_empty() or low_signal.is_empty():
        return 0.0
    high_signal_rate = float(
        high_signal.select(pl.mean(PayrollCol.OBSERVED_CORRECTION)).item() or 0.0,
    )
    low_signal_rate = float(
        low_signal.select(pl.mean(PayrollCol.OBSERVED_CORRECTION)).item() or 0.0,
    )
    return round(high_signal_rate - low_signal_rate, 4)


def _metric_unit_rows(
    scenario_name: str,
    scenario: ScenarioSpec,
    seed: int,
    model_name: str,
    budget: float,
    metrics: dict[str, float | str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    display_name = str(scenario.metadata.get("display_name", scenario.name))
    for metric_name in SCENARIO_BENCHMARK_METRICS:
        value = metrics.get(metric_name)
        if value is None:
            continue
        rows.append(
            {
                "scenario": scenario_name,
                "display_name": display_name,
                "seed": seed,
                "unit": _benchmark_unit_name(scenario_name, seed),
                "model": model_name,
                MetricCol.K: budget,
                "review_budget_label": _format_review_budget_pct(budget),
                "metric": metric_name,
                "value": float(value),
            },
        )
    return rows


def _winner_frequency(metric_units: pl.DataFrame) -> pl.DataFrame:
    if metric_units.is_empty():
        return pl.DataFrame()
    objective_map = pl.DataFrame(
        {
            "objective": [objective for objective, _ in SCENARIO_BENCHMARK_OBJECTIVES],
            "metric": [metric for _, metric in SCENARIO_BENCHMARK_OBJECTIVES],
        },
    )
    with_objectives = metric_units.join(objective_map, on="metric", how="inner")
    winners = (
        with_objectives.sort(
            ["objective", MetricCol.K, "unit", "value", "model"],
            descending=[False, False, False, True, False],
        )
        .group_by(["objective", MetricCol.K, "unit"], maintain_order=True)
        .head(1)
    )
    total_units = max(winners.select(pl.n_unique("unit")).item() or 0, 1)
    return (
        winners.group_by(["objective", MetricCol.K, "review_budget_label", "model"])
        .agg(
            pl.len().alias("win_count"),
            (pl.len() / total_units).round(4).alias("win_frequency"),
        )
        .sort(
            ["objective", MetricCol.K, "win_count", "model"],
            descending=[False, False, True, False],
        )
    )


def _median_metric_summary(metric_units: pl.DataFrame) -> pl.DataFrame:
    if metric_units.is_empty():
        return pl.DataFrame()
    return (
        metric_units.group_by(["model", MetricCol.K, "review_budget_label", "metric"])
        .agg(
            pl.median("value").alias("median"),
            pl.col("value").quantile(0.10).alias("lower_interval"),
            pl.col("value").quantile(0.90).alias("upper_interval"),
            pl.len().alias("study_units"),
        )
        .sort(
            ["metric", MetricCol.K, "median", "model"],
            descending=[False, False, True, False],
        )
    )


def _winner_map(metric_units: pl.DataFrame) -> pl.DataFrame:
    if metric_units.is_empty():
        return pl.DataFrame()
    objective_map = pl.DataFrame(
        {
            "objective": [objective for objective, _ in SCENARIO_BENCHMARK_OBJECTIVES],
            "metric": [metric for _, metric in SCENARIO_BENCHMARK_OBJECTIVES],
        },
    )
    summary = _median_metric_summary(metric_units).join(
        objective_map,
        on="metric",
        how="inner",
    )
    return (
        summary.sort(
            ["objective", MetricCol.K, "median", "model"],
            descending=[False, False, True, False],
        )
        .group_by(
            ["objective", MetricCol.K, "review_budget_label"],
            maintain_order=True,
        )
        .head(1)
        .rename({"median": "selection_value", "model": "winner"})
        .sort(["objective", MetricCol.K])
    )
