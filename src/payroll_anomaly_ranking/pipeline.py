from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar

import polars as pl

from payroll_anomaly_ranking.columns import OutputName, PayrollCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import generate_employee_pay_cycles, generate_payroll
from payroll_anomaly_ranking.evaluation import (
    backtest_by_period,
    employee_cycle_backtest_by_period,
    evaluate_employee_cycle_scores,
    evaluate_scores,
    leakage_checks,
    leakage_checks_for_features,
    rolling_origin_evaluation,
)
from payroll_anomaly_ranking.explainability import (
    build_employee_cycle_evaluation_review_queue,
    build_employee_cycle_facility_summary,
    build_employee_cycle_review_queue,
    build_evaluation_review_queue,
    build_facility_approval_summary,
    build_review_queue,
)
from payroll_anomaly_ranking.features import build_features
from payroll_anomaly_ranking.models import score_employee_pay_cycles, score_payroll
from payroll_anomaly_ranking.rules import add_rule_flags
from payroll_anomaly_ranking.scenarios import ScenarioSpec
from payroll_anomaly_ranking.validation import (
    PayrollAggregations,
    payroll_aggregations,
    validate_employee_pay_cycles,
    validate_payroll,
)

T = TypeVar("T")


@dataclass(frozen=True)
class PipelineIncludeConfig:
    validation: bool = True
    aggregations: bool = True
    evaluation: bool = True
    backtest: bool = True
    rolling_origin: bool = True
    review_queues: bool = True
    leakage_checks: bool = True

    @classmethod
    def all(cls) -> PipelineIncludeConfig:
        return cls()

    @classmethod
    def scored_only(cls) -> PipelineIncludeConfig:
        return cls(
            validation=False,
            aggregations=False,
            evaluation=False,
            backtest=False,
            rolling_origin=False,
            review_queues=False,
            leakage_checks=False,
        )


class PipelineArtifactNotGeneratedError(RuntimeError):
    """Raised when code accesses a pipeline artifact that was not requested."""


def _artifact_not_generated(artifact_name: str) -> PipelineArtifactNotGeneratedError:
    return PipelineArtifactNotGeneratedError(
        f"Pipeline artifact '{artifact_name}' was not generated. "
        "Include it via PipelineIncludeConfig before accessing this result.",
    )


@dataclass(frozen=True)
class PipelineResults:
    payroll: pl.DataFrame
    labels: pl.DataFrame
    scored: pl.DataFrame
    scenario_metadata: dict[str, object]
    include: PipelineIncludeConfig = PipelineIncludeConfig()
    _validation_failures: pl.DataFrame | None = None
    _validation_warnings: pl.DataFrame | None = None
    _aggregations: PayrollAggregations | None = None
    _metrics: pl.DataFrame | None = None
    _model_comparison: pl.DataFrame | None = None
    _category_error_analysis: pl.DataFrame | None = None
    _uncertainty_bucket_metrics: pl.DataFrame | None = None
    _risk_coverage_analysis: pl.DataFrame | None = None
    _expected_gross_pay_interval_metrics: pl.DataFrame | None = None
    _production_candidacy: pl.DataFrame | None = None
    _backtest: pl.DataFrame | None = None
    _rolling_origin_metrics: pl.DataFrame | None = None
    _validation_selected_settings: pl.DataFrame | None = None
    _stability_summary: pl.DataFrame | None = None
    _leakage_checks: pl.DataFrame | None = None
    _analyst_review_queue: pl.DataFrame | None = None
    _evaluation_labeled_review_queue: pl.DataFrame | None = None
    _facility_approval_summary: pl.DataFrame | None = None

    def _required(self, value: T | None, artifact_name: str) -> T:
        if value is None:
            raise _artifact_not_generated(artifact_name)
        return value

    @property
    def validation_failures(self) -> pl.DataFrame:
        return self._required(self._validation_failures, "validation_failures")

    @property
    def validation_warnings(self) -> pl.DataFrame:
        return self._required(self._validation_warnings, "validation_warnings")

    @property
    def aggregations(self) -> PayrollAggregations:
        return self._required(self._aggregations, "aggregations")

    @property
    def metrics(self) -> pl.DataFrame:
        return self._required(self._metrics, "metrics")

    @property
    def model_comparison(self) -> pl.DataFrame:
        return self._required(self._model_comparison, "model_comparison")

    @property
    def category_error_analysis(self) -> pl.DataFrame:
        return self._required(self._category_error_analysis, "category_error_analysis")

    @property
    def uncertainty_bucket_metrics(self) -> pl.DataFrame:
        return self._required(
            self._uncertainty_bucket_metrics,
            "uncertainty_bucket_metrics",
        )

    @property
    def risk_coverage_analysis(self) -> pl.DataFrame:
        return self._required(self._risk_coverage_analysis, "risk_coverage_analysis")

    @property
    def expected_gross_pay_interval_metrics(self) -> pl.DataFrame:
        return self._required(
            self._expected_gross_pay_interval_metrics,
            "expected_gross_pay_interval_metrics",
        )

    @property
    def production_candidacy(self) -> pl.DataFrame:
        return self._required(self._production_candidacy, "production_candidacy")

    @property
    def backtest(self) -> pl.DataFrame:
        return self._required(self._backtest, "backtest")

    @property
    def rolling_origin_metrics(self) -> pl.DataFrame:
        return self._required(self._rolling_origin_metrics, "rolling_origin_metrics")

    @property
    def validation_selected_settings(self) -> pl.DataFrame:
        return self._required(
            self._validation_selected_settings,
            "validation_selected_settings",
        )

    @property
    def stability_summary(self) -> pl.DataFrame:
        return self._required(self._stability_summary, "stability_summary")

    @property
    def leakage_checks(self) -> pl.DataFrame:
        return self._required(self._leakage_checks, "leakage_checks")

    @property
    def analyst_review_queue(self) -> pl.DataFrame:
        return self._required(self._analyst_review_queue, "analyst_review_queue")

    @property
    def evaluation_labeled_review_queue(self) -> pl.DataFrame:
        return self._required(
            self._evaluation_labeled_review_queue,
            "evaluation_labeled_review_queue",
        )

    @property
    def facility_approval_summary(self) -> pl.DataFrame:
        return self._required(
            self._facility_approval_summary,
            "facility_approval_summary",
        )


def run_legacy_shift_pipeline(
    config: PayrollConfig = PayrollConfig(),
    *,
    scenario: ScenarioSpec | None = None,
    write_outputs: bool = False,
    include: PipelineIncludeConfig = PipelineIncludeConfig(),
) -> PipelineResults:
    generated = generate_payroll(config, scenario=scenario)
    features = build_features(generated.payroll)
    ruled = add_rule_flags(features)
    scored = score_payroll(ruled, config)
    validation = validate_payroll(generated.payroll) if include.validation else None
    aggregations = (
        payroll_aggregations(generated.payroll) if include.aggregations else None
    )
    evaluation = evaluate_scores(scored, config) if include.evaluation else None
    category = (
        evaluation.category_error_analysis.sort(PayrollCol.ANOMALY_CATEGORY)
        if evaluation is not None
        else None
    )
    backtest = backtest_by_period(scored, config) if include.backtest else None
    analyst_queue = (
        build_review_queue(scored, top_k=max(config.review_budgets))
        if include.review_queues or include.leakage_checks
        else None
    )
    evaluation_queue = (
        build_evaluation_review_queue(
            scored,
            top_k=max(config.review_budgets),
        )
        if include.review_queues
        else None
    )
    facility_summary = (
        build_facility_approval_summary(scored, top_k=max(config.review_budgets))
        if include.review_queues
        else None
    )
    rolling = (
        rolling_origin_evaluation(scored, config) if include.rolling_origin else None
    )
    leakage = (
        leakage_checks(analyst_queue)
        if include.leakage_checks and analyst_queue is not None
        else None
    )
    results = PipelineResults(
        payroll=generated.payroll,
        labels=generated.labels,
        scored=scored,
        scenario_metadata=generated.metadata or _scenario_metadata(scenario),
        include=include,
        _validation_failures=validation.failures if validation is not None else None,
        _validation_warnings=validation.warnings if validation is not None else None,
        _aggregations=aggregations,
        _metrics=evaluation.metrics if evaluation is not None else None,
        _model_comparison=evaluation.model_comparison
        if evaluation is not None
        else None,
        _category_error_analysis=category,
        _uncertainty_bucket_metrics=evaluation.uncertainty_bucket_metrics
        if evaluation is not None
        else None,
        _risk_coverage_analysis=evaluation.risk_coverage_analysis
        if evaluation is not None
        else None,
        _expected_gross_pay_interval_metrics=evaluation.expected_gross_pay_interval_metrics
        if evaluation is not None
        else None,
        _production_candidacy=evaluation.production_candidacy
        if evaluation is not None
        else None,
        _backtest=backtest,
        _rolling_origin_metrics=rolling.metrics if rolling is not None else None,
        _validation_selected_settings=rolling.selected_settings
        if rolling is not None
        else None,
        _stability_summary=rolling.stability_summary if rolling is not None else None,
        _leakage_checks=leakage,
        _analyst_review_queue=analyst_queue if include.review_queues else None,
        _evaluation_labeled_review_queue=evaluation_queue,
        _facility_approval_summary=facility_summary,
    )
    if write_outputs:
        write_pipeline_outputs(results, config)
    return results


def run_employee_cycle_pipeline(
    config: PayrollConfig = PayrollConfig(),
    *,
    scenario: ScenarioSpec | None = None,
    write_outputs: bool = False,
    include: PipelineIncludeConfig = PipelineIncludeConfig(),
) -> PipelineResults:
    generated = generate_employee_pay_cycles(config, scenario=scenario)
    scoring = score_employee_pay_cycles(generated.payroll, config)
    scored = scoring.scored
    validation = (
        validate_employee_pay_cycles(generated.payroll) if include.validation else None
    )
    aggregations = (
        payroll_aggregations(generated.supporting_payroll)
        if include.aggregations
        else None
    )
    evaluation = (
        evaluate_employee_cycle_scores(scored, config) if include.evaluation else None
    )
    category = (
        evaluation.category_error_analysis.sort(PayrollCol.ANOMALY_CATEGORY)
        if evaluation is not None
        else None
    )
    backtest = (
        employee_cycle_backtest_by_period(scored, config) if include.backtest else None
    )
    analyst_queue = (
        build_employee_cycle_review_queue(
            scored,
            top_k=_employee_cycle_queue_budget(config),
        )
        if include.review_queues or include.leakage_checks
        else None
    )
    evaluation_queue = (
        build_employee_cycle_evaluation_review_queue(
            scored,
            top_k=_employee_cycle_queue_budget(config),
        )
        if include.review_queues
        else None
    )
    facility_summary = (
        build_employee_cycle_facility_summary(
            scored,
            top_k=_employee_cycle_queue_budget(config),
        )
        if include.review_queues
        else None
    )
    rolling = (
        rolling_origin_evaluation(scored, config) if include.rolling_origin else None
    )
    leakage = (
        leakage_checks_for_features(analyst_queue, scoring.feature_columns)
        if include.leakage_checks and analyst_queue is not None
        else None
    )
    results = PipelineResults(
        payroll=generated.payroll,
        labels=generated.labels,
        scored=scored,
        scenario_metadata=generated.metadata or _scenario_metadata(scenario),
        include=include,
        _validation_failures=validation.failures if validation is not None else None,
        _validation_warnings=validation.warnings if validation is not None else None,
        _aggregations=aggregations,
        _metrics=evaluation.metrics if evaluation is not None else None,
        _model_comparison=evaluation.model_comparison
        if evaluation is not None
        else None,
        _category_error_analysis=category,
        _uncertainty_bucket_metrics=evaluation.uncertainty_bucket_metrics
        if evaluation is not None
        else None,
        _risk_coverage_analysis=evaluation.risk_coverage_analysis
        if evaluation is not None
        else None,
        _expected_gross_pay_interval_metrics=evaluation.expected_gross_pay_interval_metrics
        if evaluation is not None
        else None,
        _production_candidacy=evaluation.production_candidacy
        if evaluation is not None
        else None,
        _backtest=backtest,
        _rolling_origin_metrics=rolling.metrics if rolling is not None else None,
        _validation_selected_settings=rolling.selected_settings
        if rolling is not None
        else None,
        _stability_summary=rolling.stability_summary if rolling is not None else None,
        _leakage_checks=leakage,
        _analyst_review_queue=analyst_queue if include.review_queues else None,
        _evaluation_labeled_review_queue=evaluation_queue,
        _facility_approval_summary=facility_summary,
    )
    if write_outputs:
        write_pipeline_outputs(results, config)
    return results


def _employee_cycle_queue_budget(config: PayrollConfig) -> float:
    if config.employee_cycle_review_budget_percents is not None:
        return max(config.employee_cycle_review_budget_percents)
    return float(max(config.review_budgets))


def run_pipeline(
    config: PayrollConfig = PayrollConfig(),
    *,
    scenario: ScenarioSpec | None = None,
    write_outputs: bool = False,
    include: PipelineIncludeConfig = PipelineIncludeConfig(),
) -> PipelineResults:
    return run_employee_cycle_pipeline(
        config,
        scenario=scenario,
        write_outputs=write_outputs,
        include=include,
    )


run_shift_level_pipeline = run_legacy_shift_pipeline


def write_pipeline_outputs(
    results: PipelineResults,
    config: PayrollConfig = PayrollConfig(),
) -> None:
    _require_output_artifacts(results)
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir = config.output_dir / "evaluation"
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    results.payroll.write_csv(config.data_dir / "synthetic_payroll.csv")
    if PayrollCol.SHIFT_ID in results.payroll.columns:
        results.payroll.write_csv(config.data_dir / "synthetic_snf_shift_payroll.csv")
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
    results.analyst_review_queue.write_csv(
        evaluation_dir / OutputName.ADMIN_APPROVAL_QUEUE,
    )
    results.evaluation_labeled_review_queue.write_csv(
        evaluation_dir / OutputName.EVALUATION_LABELED_REVIEW_QUEUE,
    )
    results.facility_approval_summary.write_csv(
        evaluation_dir / OutputName.FACILITY_APPROVAL_SUMMARY,
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


def _require_output_artifacts(results: PipelineResults) -> None:
    for artifact_name in (
        "metrics",
        "model_comparison",
        "category_error_analysis",
        "uncertainty_bucket_metrics",
        "risk_coverage_analysis",
        "expected_gross_pay_interval_metrics",
        "backtest",
        "rolling_origin_metrics",
        "validation_selected_settings",
        "stability_summary",
        "leakage_checks",
        "analyst_review_queue",
        "evaluation_labeled_review_queue",
        "facility_approval_summary",
    ):
        getattr(results, artifact_name)


if __name__ == "__main__":
    run_pipeline(write_outputs=True)
