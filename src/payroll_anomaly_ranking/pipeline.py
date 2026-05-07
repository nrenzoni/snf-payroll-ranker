from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from payroll_anomaly_ranking.columns import OutputName, PayrollCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import generate_payroll
from payroll_anomaly_ranking.evaluation import (
    backtest_by_period,
    evaluate_scores,
    leakage_checks,
    rolling_origin_evaluation,
)
from payroll_anomaly_ranking.explainability import (
    build_evaluation_review_queue,
    build_review_queue,
)
from payroll_anomaly_ranking.features import build_features
from payroll_anomaly_ranking.models import score_payroll
from payroll_anomaly_ranking.rules import add_rule_flags
from payroll_anomaly_ranking.scenarios import ScenarioSpec
from payroll_anomaly_ranking.validation import (
    PayrollAggregations,
    payroll_aggregations,
    validate_payroll,
)


@dataclass(frozen=True)
class PipelineResults:
    payroll: pl.DataFrame
    labels: pl.DataFrame
    validation_failures: pl.DataFrame
    validation_warnings: pl.DataFrame
    aggregations: PayrollAggregations
    scored: pl.DataFrame
    metrics: pl.DataFrame
    model_comparison: pl.DataFrame
    category_error_analysis: pl.DataFrame
    uncertainty_bucket_metrics: pl.DataFrame
    risk_coverage_analysis: pl.DataFrame
    expected_gross_pay_interval_metrics: pl.DataFrame
    backtest: pl.DataFrame
    rolling_origin_metrics: pl.DataFrame
    validation_selected_settings: pl.DataFrame
    stability_summary: pl.DataFrame
    leakage_checks: pl.DataFrame
    analyst_review_queue: pl.DataFrame
    evaluation_labeled_review_queue: pl.DataFrame
    scenario_metadata: dict[str, object]


def run_pipeline(
    config: PayrollConfig = PayrollConfig(),
    *,
    scenario: ScenarioSpec | None = None,
    write_outputs: bool = False,
) -> PipelineResults:
    generated = generate_payroll(config, scenario=scenario)
    validation = validate_payroll(generated.payroll)
    features = build_features(generated.payroll)
    ruled = add_rule_flags(features)
    scored = score_payroll(ruled, config)
    evaluation = evaluate_scores(scored, config)
    category = evaluation.category_error_analysis.sort(PayrollCol.ANOMALY_CATEGORY)
    backtest = backtest_by_period(scored, config)
    analyst_queue = build_review_queue(scored, top_k=max(config.review_budgets))
    evaluation_queue = build_evaluation_review_queue(
        scored,
        top_k=max(config.review_budgets),
    )
    rolling = rolling_origin_evaluation(
        scored,
        config,
    )
    leakage = leakage_checks(analyst_queue)
    results = PipelineResults(
        payroll=generated.payroll,
        labels=generated.labels,
        validation_failures=validation.failures,
        validation_warnings=validation.warnings,
        aggregations=payroll_aggregations(generated.payroll),
        scored=scored,
        metrics=evaluation.metrics,
        model_comparison=evaluation.model_comparison,
        category_error_analysis=category,
        uncertainty_bucket_metrics=evaluation.uncertainty_bucket_metrics,
        risk_coverage_analysis=evaluation.risk_coverage_analysis,
        expected_gross_pay_interval_metrics=evaluation.expected_gross_pay_interval_metrics,
        backtest=backtest,
        rolling_origin_metrics=rolling.metrics,
        validation_selected_settings=rolling.selected_settings,
        stability_summary=rolling.stability_summary,
        leakage_checks=leakage,
        analyst_review_queue=analyst_queue,
        evaluation_labeled_review_queue=evaluation_queue,
        scenario_metadata=_scenario_metadata(scenario),
    )
    if write_outputs:
        write_pipeline_outputs(results, config)
    return results


def write_pipeline_outputs(
    results: PipelineResults,
    config: PayrollConfig = PayrollConfig(),
) -> None:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir = config.output_dir / "evaluation"
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    results.payroll.write_csv(config.data_dir / "synthetic_payroll.csv")
    results.labels.write_csv(config.data_dir / "synthetic_payroll_labels.csv")
    results.scored.write_csv(evaluation_dir / "scored_payroll.csv")
    results.metrics.write_csv(evaluation_dir / "review_budget_metrics.csv")
    results.model_comparison.write_csv(evaluation_dir / "model_comparison.csv")
    results.category_error_analysis.write_csv(
        evaluation_dir / "category_error_analysis.csv",
    )
    results.uncertainty_bucket_metrics.write_csv(
        evaluation_dir / "uncertainty_bucket_metrics.csv",
    )
    results.risk_coverage_analysis.write_csv(
        evaluation_dir / "risk_coverage_analysis.csv",
    )
    results.expected_gross_pay_interval_metrics.write_csv(
        evaluation_dir / "expected_gross_pay_interval_metrics.csv",
    )
    results.backtest.write_csv(evaluation_dir / "backtest_metrics.csv")
    results.rolling_origin_metrics.write_csv(
        evaluation_dir / "rolling_origin_metrics.csv",
    )
    results.validation_selected_settings.write_csv(
        evaluation_dir / "validation_selected_settings.csv",
    )
    results.stability_summary.write_csv(evaluation_dir / "stability_summary.csv")
    results.leakage_checks.write_csv(evaluation_dir / "leakage_checks.csv")
    results.analyst_review_queue.write_csv(
        evaluation_dir / OutputName.ANALYST_REVIEW_QUEUE,
    )
    results.evaluation_labeled_review_queue.write_csv(
        evaluation_dir / OutputName.EVALUATION_LABELED_REVIEW_QUEUE,
    )
    scenario_metadata = results.scenario_metadata
    if scenario_metadata:
        pl.DataFrame([scenario_metadata]).write_json(
            evaluation_dir / "scenario_metadata.json",
        )


def _scenario_metadata(scenario: ScenarioSpec | None) -> dict[str, object]:
    if scenario is None:
        return {"name": "default", "controls_applied": False}
    metadata = scenario.to_metadata()
    metadata["controls_applied"] = bool(
        scenario.anomaly_plan or scenario.drift_plans or scenario.change_points,
    )
    return metadata


if __name__ == "__main__":
    run_pipeline(write_outputs=True)
