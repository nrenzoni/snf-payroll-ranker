import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, cast

import polars as pl
import pytest

from payroll_anomaly_ranking.columns import (
    MODEL_FEATURE_COLUMNS,
    FeatureCol,
    MetricCol,
    OutputName,
    PayrollCol,
    ReviewCol,
    RuleCol,
    ScoreCol,
)
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import (
    employee_cycle_hard_rule_funnel,
    employee_cycle_residual_diagnostics,
    generate_employee_pay_cycles,
    generate_payroll,
    scenario_sanity_summary,
    scenario_summary,
)
from payroll_anomaly_ranking.diagnostics import (
    business_proof_hybrid_win_rates,
    business_proof_metric_intervals,
    business_proof_ranking_units,
    business_proof_threshold_units,
    calibration_plot_inputs,
    expected_pay_calibration,
    pairwise_component_superiority,
    review_budget_interval_summary,
    run_diagnostic_comparison_units,
    subgroup_diagnostics,
    top_subgroup_diagnostics,
)
from payroll_anomaly_ranking.evaluation import (
    employee_cycle_feature_ablation,
    employee_cycle_issue_type_model_performance,
    employee_cycle_label_ablation,
    employee_cycle_severe_miss_examples,
    employee_cycle_training_universe_ablation,
    evaluate_employee_cycle_scores,
    evaluate_scores,
    leakage_checks,
    rolling_origin_evaluation,
)
from payroll_anomaly_ranking.explainability import (
    build_employee_cycle_review_queue,
    build_evaluation_review_queue,
    build_review_queue,
)
from payroll_anomaly_ranking.features import (
    build_employee_cycle_features,
    build_features,
)
from payroll_anomaly_ranking.models import (
    _feature_matrix,
    score_employee_pay_cycles,
    score_featured_employee_pay_cycles,
    score_payroll,
)
from payroll_anomaly_ranking.pipeline import (
    PipelineArtifactNotGeneratedError,
    PipelineIncludeConfig,
    run_employee_cycle_pipeline,
    run_pipeline,
    run_shift_level_pipeline,
)
from payroll_anomaly_ranking.queue_simulation import (
    simulate_queue_capacity,
    summarize_queue_simulation,
)
from payroll_anomaly_ranking.rules import add_rule_flags
from payroll_anomaly_ranking.scenarios import (
    AnomalyPlan,
    ChangePointEvent,
    DriftPlan,
    QueueSimulationSpec,
    ScenarioSpec,
    TargetedAnomalyControl,
    diagnostic_scenario_presets,
)
from payroll_anomaly_ranking.validation import (
    validate_employee_pay_cycles,
    validate_payroll,
)

pytestmark = pytest.mark.integration


def _load_notebook_plots_module() -> Any:
    module_path = Path("notebooks/common/plots.py")
    spec = importlib.util.spec_from_file_location("notebook_common_plots", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_end_to_end_smoke() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    generated = generate_payroll(config)
    validation = validate_payroll(generated.payroll)
    featured = build_features(generated.payroll)
    ruled = add_rule_flags(featured)
    scored = score_payroll(ruled, config)
    evaluation = evaluate_scores(scored, config)
    queue = build_review_queue(scored, top_k=10)

    assert generated.payroll.height > 0
    assert generated.labels.height > 0
    assert validation.failures.height == 0
    assert validation.warnings.height >= 0
    assert "final_anomaly_score" in scored.columns
    assert evaluation.metrics.height == 2
    assert evaluation.model_comparison.height == 6
    assert evaluation.category_error_analysis.height > 0
    assert evaluation.uncertainty_bucket_metrics.height > 0
    assert evaluation.risk_coverage_analysis.height > 0
    assert evaluation.expected_gross_pay_interval_metrics.height == 1
    assert queue.height > 0
    assert not {"name", "email", "bank_account", "ssn"} & set(generated.payroll.columns)


def test_pipeline_writes_outputs_only_when_requested(tmp_path) -> None:
    config = PayrollConfig(
        employee_count=80,
        pay_periods=10,
        review_budgets=(5, 10),
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "outputs",
    )

    run_pipeline(config)

    assert not config.data_dir.exists()
    assert not config.output_dir.exists()

    run_pipeline(config, write_outputs=True)

    assert (config.data_dir / "synthetic_payroll.csv").exists()
    assert (config.data_dir / "synthetic_payroll_labels.csv").exists()
    assert not (config.data_dir / "synthetic_snf_shift_payroll.csv").exists()
    assert (config.output_dir / "evaluation" / "category_error_analysis.csv").exists()
    assert (
        config.output_dir / "evaluation" / "uncertainty_bucket_metrics.csv"
    ).exists()
    assert (config.output_dir / "evaluation" / "risk_coverage_analysis.csv").exists()
    assert (
        config.output_dir / "evaluation" / "expected_gross_pay_interval_metrics.csv"
    ).exists()
    assert (config.output_dir / "evaluation" / "rolling_origin_metrics.csv").exists()
    assert (
        config.output_dir / "evaluation" / "validation_selected_settings.csv"
    ).exists()
    assert (config.output_dir / "evaluation" / "stability_summary.csv").exists()
    assert (config.output_dir / "evaluation" / "leakage_checks.csv").exists()
    assert (config.output_dir / "evaluation" / OutputName.ANALYST_REVIEW_QUEUE).exists()
    assert (
        config.output_dir / "evaluation" / OutputName.EVALUATION_LABELED_REVIEW_QUEUE
    ).exists()


def test_pipeline_default_result_exposes_full_artifacts() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))

    results = run_pipeline(config)

    assert results.payroll.height > 0
    assert results.labels.height > 0
    assert results.scored.height == results.payroll.height
    assert results.validation_failures.height == 0
    assert results.validation_warnings.height >= 0
    assert results.aggregations.payroll_volume.height > 0
    assert results.metrics.height == 2
    assert results.model_comparison.height >= 4
    assert results.category_error_analysis.height > 0
    assert results.uncertainty_bucket_metrics.height == 0
    assert results.risk_coverage_analysis.height == 0
    assert results.expected_gross_pay_interval_metrics.height > 0
    assert results.backtest.height > 0
    assert results.rolling_origin_metrics.height > 0
    assert results.validation_selected_settings.height > 0
    assert results.stability_summary.height == 1
    assert results.leakage_checks.height > 0
    assert results.analyst_review_queue.height > 0
    assert results.evaluation_labeled_review_queue.height > 0
    assert results.facility_approval_summary.height > 0
    assert results.scenario_metadata["name"] == "default"
    assert PayrollCol.EMPLOYEE_PAY_CYCLE_ID in results.payroll.columns
    assert PayrollCol.SHIFT_ID not in results.payroll.columns


def test_pipeline_scored_only_result_exposes_core_artifacts() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))

    results = run_pipeline(config, include=PipelineIncludeConfig.scored_only())

    assert results.payroll.height > 0
    assert results.labels.height > 0
    assert results.scored.height == results.payroll.height
    assert results.scenario_metadata["name"] == "default"


def test_pipeline_scored_only_excluded_artifacts_raise() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    results = run_pipeline(config, include=PipelineIncludeConfig.scored_only())

    excluded_artifact_names = [
        "validation_failures",
        "validation_warnings",
        "aggregations",
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
    ]
    for artifact_name in excluded_artifact_names:
        with pytest.raises(PipelineArtifactNotGeneratedError, match=artifact_name):
            getattr(results, artifact_name)


def test_default_payroll_generation_reproducible_and_schema_compatible() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))

    generated_a = generate_payroll(config)
    generated_b = generate_payroll(config)
    validation = validate_payroll(generated_a.payroll)

    assert generated_a.payroll.equals(generated_b.payroll)
    assert generated_a.labels.equals(generated_b.labels)
    assert validation.failures.height == 0
    assert {
        PayrollCol.SHIFT_ID,
        PayrollCol.FACILITY_ID,
        PayrollCol.UNIT,
        PayrollCol.ROLE,
        PayrollCol.SHIFT_TYPE,
        PayrollCol.PAY_CODE_CATEGORY,
        PayrollCol.PREMIUM_PAY,
        PayrollCol.IS_ANOMALY,
        PayrollCol.ANOMALY_CATEGORY,
        PayrollCol.ANOMALY_DOLLARS,
    } <= set(generated_a.payroll.columns)


def test_scenario_generation_is_reproducible_with_same_seed() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scenario = ScenarioSpec(
        name="mix_shift",
        anomaly_plan=AnomalyPlan(
            category_weights={"overtime_spike": 1.0},
            target_count=12,
        ),
    )

    generated_a = generate_payroll(config, scenario=scenario)
    generated_b = generate_payroll(config, scenario=scenario)

    assert generated_a.payroll.equals(generated_b.payroll)
    assert generated_a.labels.equals(generated_b.labels)
    assert generated_a.labels.get_column(
        PayrollCol.ANOMALY_CATEGORY,
    ).unique().to_list() == [
        "overtime_spike",
    ]


def test_employee_pay_cycle_generation_is_reproducible_and_schema_valid() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))

    generated_a = generate_employee_pay_cycles(config)
    generated_b = generate_employee_pay_cycles(config)
    validation = validate_employee_pay_cycles(generated_a.payroll)

    assert generated_a.payroll.equals(generated_b.payroll)
    assert generated_a.labels.equals(generated_b.labels)
    assert validation.failures.height == 0
    assert {
        PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
        PayrollCol.EMPLOYEE_ID,
        PayrollCol.FACILITY_ID,
        PayrollCol.PAY_PERIOD_INDEX,
        PayrollCol.TOTAL_GROSS_PAY,
        PayrollCol.TOTAL_PAID_HOURS,
        PayrollCol.SHIFT_COUNT,
        PayrollCol.IS_ANOMALY,
        PayrollCol.ANOMALY_CATEGORY,
        PayrollCol.ANOMALY_DOLLARS,
        PayrollCol.RELEVANCE_GRADE,
        PayrollCol.NET_UTILITY,
    } <= set(generated_a.payroll.columns)


def test_employee_pay_cycle_rows_reconcile_to_supporting_shift_detail() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    generated = generate_employee_pay_cycles(config)

    supporting = generated.supporting_payroll.group_by(
        [PayrollCol.EMPLOYEE_ID, PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX],
    ).agg(
        pl.len().alias("shift_count"),
        pl.sum(PayrollCol.GROSS_PAY).alias("total_gross_pay"),
        pl.sum(PayrollCol.PAID_HOURS).alias("total_paid_hours"),
        pl.sum(PayrollCol.IS_ANOMALY).alias("anomalous_shift_count"),
        pl.sum(PayrollCol.ANOMALY_DOLLARS).alias("anomaly_dollars"),
    )
    reconciled = generated.payroll.join(
        supporting,
        on=[
            PayrollCol.EMPLOYEE_ID,
            PayrollCol.FACILITY_ID,
            PayrollCol.PAY_PERIOD_INDEX,
        ],
        how="inner",
    )

    assert reconciled.height == generated.payroll.height
    assert reconciled.select(
        (pl.col(PayrollCol.SHIFT_COUNT) == pl.col("shift_count")).all(),
        (
            pl.col(PayrollCol.TOTAL_GROSS_PAY).round(2)
            == pl.col("total_gross_pay").round(2)
        ).all(),
        (
            pl.col(PayrollCol.TOTAL_PAID_HOURS).round(2)
            == pl.col("total_paid_hours").round(2)
        ).all(),
        (
            pl.col(PayrollCol.ANOMALOUS_SHIFT_COUNT) == pl.col("anomalous_shift_count")
        ).all(),
        (
            pl.col(PayrollCol.ANOMALY_DOLLARS).round(2)
            == pl.col("anomaly_dollars").round(2)
        ).all(),
    ).row(0) == (True, True, True, True, True)


def test_employee_pay_cycle_labels_capture_only_anomalous_cycles() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    generated = generate_employee_pay_cycles(config)

    assert generated.labels.height > 0
    assert generated.labels.select(pl.col(PayrollCol.IS_ANOMALY).min()).item() == 1
    assert (
        generated.labels.join(
            generated.payroll.select(
                PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
                PayrollCol.IS_ANOMALY,
                PayrollCol.ANOMALY_DOLLARS,
                PayrollCol.RELEVANCE_GRADE,
                PayrollCol.NET_UTILITY,
            ),
            on=PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
            how="inner",
        ).height
        == generated.labels.height
    )


def test_employee_cycle_label_engineering_produces_bounded_relevance_and_utility() -> (
    None
):
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_employee_pay_cycles(config).payroll

    assert payroll.select(pl.col(PayrollCol.RELEVANCE_GRADE).min()).item() >= 0
    assert payroll.select(pl.col(PayrollCol.RELEVANCE_GRADE).max()).item() <= 3
    assert (
        payroll.filter(pl.col(PayrollCol.IS_ANOMALY) == 0)
        .select(pl.col(PayrollCol.RELEVANCE_GRADE).max())
        .item()
        == 0
    )
    assert (
        payroll.filter(pl.col(PayrollCol.Y_ISSUE) == 1)
        .select(pl.col(PayrollCol.NET_UTILITY).min())
        .item()
        > -18.0
    )
    assert (
        payroll.filter(pl.col(PayrollCol.IS_ANOMALY) == 0)
        .select(pl.col(PayrollCol.NET_UTILITY).min())
        .item()
        == -18.0
    )
    assert {PayrollCol.CRITICAL_HARD_RULE_FLAG, PayrollCol.RESIDUAL_RECORD} <= set(
        payroll.columns,
    )
    assert {
        PayrollCol.Y_ISSUE,
        PayrollCol.Y_DOLLAR,
        PayrollCol.SEVERE_ISSUE,
        PayrollCol.RULE_MISSED_SEVERE_ISSUE,
    } <= set(payroll.columns)
    assert (
        payroll.filter(pl.col(PayrollCol.CRITICAL_HARD_RULE_FLAG) == 1)
        .select(pl.col(PayrollCol.RESIDUAL_RECORD).max())
        .item()
        == 0
    )
    assert (
        payroll.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 0)
        .select(pl.col(PayrollCol.Y_ISSUE).max())
        .item()
        == 0
    )
    assert (
        payroll.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 0)
        .select(pl.col(PayrollCol.Y_DOLLAR).max())
        .item()
        == 0.0
    )
    assert (
        payroll.select(
            (
                pl.col(PayrollCol.RULE_MISSED_SEVERE_ISSUE)
                <= pl.col(PayrollCol.SEVERE_ISSUE)
            ).all(),
        ).item()
        == 1
    )
    assert (
        payroll.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 0)
        .select(pl.col(PayrollCol.RULE_MISSED_SEVERE_ISSUE).max())
        .item()
        == 0
    )


def test_employee_cycle_residual_gate_artifacts_exist() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_employee_pay_cycles(config).payroll

    funnel = employee_cycle_hard_rule_funnel(payroll)
    diagnostics = employee_cycle_residual_diagnostics(payroll)

    assert funnel.get_column("stage").to_list() == [
        "All payroll records",
        "Critical hard-rule flagged",
        "Residual ML universe",
    ]
    assert (
        funnel.filter(pl.col("stage") == "All payroll records").row(0, named=True)[
            "records"
        ]
        == payroll.height
    )
    assert {
        "facility_residual_issue_rate",
        "facility_cycle_residual_severe_counts",
        "residual_dollar_distribution",
        "issue_type_mix",
        "residual_records_per_facility_cycle",
    } <= set(diagnostics)
    assert diagnostics["facility_residual_issue_rate"].height > 0
    assert PayrollCol.Y_DOLLAR in diagnostics["residual_dollar_distribution"].columns
    all_stage = funnel.filter(pl.col("stage") == "All payroll records").row(
        0,
        named=True,
    )
    residual_stage = funnel.filter(pl.col("stage") == "Residual ML universe").row(
        0,
        named=True,
    )
    assert residual_stage["severe_issues"] <= all_stage["severe_issues"]


def test_employee_cycle_residual_labels_and_families_are_heterogeneous() -> None:
    config = PayrollConfig(facility_count=10, employee_count=180, pay_periods=12)
    payroll = generate_employee_pay_cycles(config).payroll
    residual = payroll.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)
    positive_residual = residual.filter(pl.col(PayrollCol.Y_ISSUE) == 1)

    severe_share = float(
        positive_residual.select(pl.mean(PayrollCol.RULE_MISSED_SEVERE_ISSUE)).item()
        or 0.0,
    )
    grade_counts = {
        int(row[PayrollCol.RELEVANCE_GRADE]): int(row["len"])
        for row in positive_residual.group_by(PayrollCol.RELEVANCE_GRADE)
        .len()
        .to_dicts()
    }

    assert positive_residual.height > 0
    assert positive_residual.get_column(PayrollCol.ANOMALY_CATEGORY).n_unique() >= 4
    assert 0.01 <= severe_share <= 0.25
    assert grade_counts.get(1, 0) > 0
    assert grade_counts.get(2, 0) > 0
    assert grade_counts.get(3, 0) > 0
    assert grade_counts.get(3, 0) < positive_residual.height // 3


def test_employee_cycle_features_use_only_prior_period_history() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_employee_pay_cycles(config).payroll
    featured = build_employee_cycle_features(payroll)

    sample = (
        featured.filter(pl.col(FeatureCol.PRIOR_EMPLOYEE_PAY_PERIOD_COUNT) >= 1)
        .sort([PayrollCol.EMPLOYEE_ID, PayrollCol.PAY_PERIOD_INDEX])
        .row(0, named=True)
    )
    prior = payroll.filter(
        (pl.col(PayrollCol.EMPLOYEE_ID) == sample[PayrollCol.EMPLOYEE_ID])
        & (pl.col(PayrollCol.PAY_PERIOD_INDEX) < sample[PayrollCol.PAY_PERIOD_INDEX]),
    )

    assert (
        sample[FeatureCol.LAG_GROSS_PAY]
        == prior.sort(PayrollCol.PAY_PERIOD_INDEX).row(
            -1,
            named=True,
        )[PayrollCol.TOTAL_GROSS_PAY]
    )
    assert sample[FeatureCol.PRIOR_EMPLOYEE_PAY_PERIOD_COUNT] == prior.height


def test_employee_cycle_scoring_returns_formulation_columns() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_employee_pay_cycles(config).payroll

    results = score_employee_pay_cycles(payroll, config)

    assert {
        ScoreCol.CLASSIFICATION_SCORE,
        ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE,
        ScoreCol.REGRESSION_SCORE,
        ScoreCol.EXPECTED_VALUE_SCORE,
        ScoreCol.RANKING_SCORE,
        ScoreCol.FINAL_ANOMALY_SCORE,
        ScoreCol.PAY_PERIOD_RANK,
    } <= set(results.scored.columns)
    assert results.score_columns == (
        ScoreCol.CLASSIFICATION_SCORE,
        ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE,
        ScoreCol.REGRESSION_SCORE,
        ScoreCol.EXPECTED_VALUE_SCORE,
        ScoreCol.RANKING_SCORE,
        ScoreCol.FINAL_ANOMALY_SCORE,
    )
    assert len(results.feature_columns) > 0


def test_employee_cycle_featured_scoring_matches_direct_scoring() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_employee_pay_cycles(config).payroll
    featured = build_employee_cycle_features(payroll)

    direct = score_employee_pay_cycles(payroll, config)
    featured_results = score_featured_employee_pay_cycles(featured, config)

    assert direct.feature_columns == featured_results.feature_columns
    assert direct.score_columns == featured_results.score_columns
    assert direct.scored.select(
        PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
        ScoreCol.CLASSIFICATION_SCORE,
        ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE,
        ScoreCol.REGRESSION_SCORE,
        ScoreCol.EXPECTED_VALUE_SCORE,
        ScoreCol.RANKING_SCORE,
        ScoreCol.FINAL_ANOMALY_SCORE,
        ScoreCol.PAY_PERIOD_RANK,
    ).equals(
        featured_results.scored.select(
            PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
            ScoreCol.CLASSIFICATION_SCORE,
            ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE,
            ScoreCol.REGRESSION_SCORE,
            ScoreCol.EXPECTED_VALUE_SCORE,
            ScoreCol.RANKING_SCORE,
            ScoreCol.FINAL_ANOMALY_SCORE,
            ScoreCol.PAY_PERIOD_RANK,
        ),
    )


def test_employee_cycle_formulations_are_not_collapsed_onto_one_signal() -> None:
    config = PayrollConfig(facility_count=10, employee_count=180, pay_periods=12)
    payroll = generate_employee_pay_cycles(config).payroll

    scored = score_employee_pay_cycles(payroll, config).scored.filter(
        pl.col(PayrollCol.RESIDUAL_RECORD) == 1,
    )

    correlations = scored.select(
        pl.corr(ScoreCol.CLASSIFICATION_SCORE, ScoreCol.REGRESSION_SCORE).alias(
            "classification_vs_regression",
        ),
        pl.corr(ScoreCol.CLASSIFICATION_SCORE, ScoreCol.RANKING_SCORE).alias(
            "classification_vs_ranking",
        ),
    ).row(0, named=True)

    assert float(correlations["classification_vs_regression"] or 0.0) < 0.95
    assert float(correlations["classification_vs_ranking"] or 0.0) < 0.98


def test_employee_cycle_scoring_uses_residual_targets_not_legacy_targets() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_employee_pay_cycles(config).payroll

    baseline = score_employee_pay_cycles(payroll, config).scored
    relabeled = payroll.with_columns(
        (1 - pl.col(PayrollCol.IS_ANOMALY)).alias(PayrollCol.IS_ANOMALY),
        (pl.col(PayrollCol.ANOMALY_DOLLARS) + 999_999.0).alias(
            PayrollCol.ANOMALY_DOLLARS,
        ),
    )
    relabeled_scored = score_employee_pay_cycles(relabeled, config).scored

    assert baseline.select(
        ScoreCol.CLASSIFICATION_SCORE,
        ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE,
        ScoreCol.REGRESSION_SCORE,
        ScoreCol.EXPECTED_VALUE_SCORE,
        ScoreCol.RANKING_SCORE,
        ScoreCol.FINAL_ANOMALY_SCORE,
    ).equals(
        relabeled_scored.select(
            ScoreCol.CLASSIFICATION_SCORE,
            ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE,
            ScoreCol.REGRESSION_SCORE,
            ScoreCol.EXPECTED_VALUE_SCORE,
            ScoreCol.RANKING_SCORE,
            ScoreCol.FINAL_ANOMALY_SCORE,
        ),
    )


def test_employee_cycle_scoring_is_reproducible() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_employee_pay_cycles(config).payroll

    scored_a = score_employee_pay_cycles(payroll, config).scored
    scored_b = score_employee_pay_cycles(payroll, config).scored

    assert scored_a.select(
        PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
        ScoreCol.CLASSIFICATION_SCORE,
        ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE,
        ScoreCol.REGRESSION_SCORE,
        ScoreCol.EXPECTED_VALUE_SCORE,
        ScoreCol.RANKING_SCORE,
        ScoreCol.FINAL_ANOMALY_SCORE,
        ScoreCol.PAY_PERIOD_RANK,
    ).equals(
        scored_b.select(
            PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
            ScoreCol.CLASSIFICATION_SCORE,
            ScoreCol.COST_SENSITIVE_CLASSIFICATION_SCORE,
            ScoreCol.REGRESSION_SCORE,
            ScoreCol.EXPECTED_VALUE_SCORE,
            ScoreCol.RANKING_SCORE,
            ScoreCol.FINAL_ANOMALY_SCORE,
            ScoreCol.PAY_PERIOD_RANK,
        ),
    )


def test_employee_cycle_evaluation_reports_grouped_metrics() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_employee_pay_cycles(config).payroll
    scored = score_employee_pay_cycles(payroll, config).scored

    evaluation = evaluate_employee_cycle_scores(scored, config)

    assert evaluation.metrics.height == len(config.review_budgets)
    assert {
        MetricCol.PRECISION_AT_K,
        MetricCol.RECALL_AT_K,
        MetricCol.RESIDUAL_NDCG_AT_K,
        MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K,
        MetricCol.REVIEWER_YIELD_AT_K,
        MetricCol.MEAN_RECIPROCAL_RANK,
        MetricCol.DOLLAR_CAPTURE_RATE,
        MetricCol.NET_UTILITY_CAPTURED_AT_K,
        MetricCol.INCREMENTAL_UTILITY_AT_K,
        MetricCol.UTILITY_PER_REVIEW,
    } <= set(evaluation.metrics.columns)
    assert evaluation.model_comparison.height >= 4
    assert evaluation.production_candidacy.height >= 1


def test_employee_cycle_ablation_helpers_return_runtime_backed_outputs() -> None:
    config = PayrollConfig(
        facility_count=12,
        employee_count=180,
        pay_periods=12,
        employee_cycle_review_budget_percents=(0.05, 0.10),
    )
    payroll = generate_employee_pay_cycles(config).payroll
    scored = score_employee_pay_cycles(payroll, config).scored

    feature_ablation = employee_cycle_feature_ablation(payroll, config)
    training_ablation = employee_cycle_training_universe_ablation(payroll, config)
    label_ablation = employee_cycle_label_ablation(scored, config)

    assert {"raw_payroll", "employee_history", "facility_role_baseline"} <= set(
        feature_ablation.get_column("feature_set").to_list(),
    )
    assert {
        "all_records",
        "residual_records_only",
        "all_records_with_gate_feature",
    } <= set(training_ablation.get_column("training_universe").to_list())
    assert {
        "holdout_period_start",
        "holdout_period_end",
        "train_records",
        "train_residual_records",
        "train_hard_rule_share",
    } <= set(training_ablation.columns)
    assert (
        training_ablation.get_column("holdout_period_end")
        >= training_ablation.get_column("holdout_period_start")
    ).all()
    assert {
        "binary_issue",
        "dollar_impact",
        "graded_relevance",
        "utility_label",
        "observed_historical_label",
        "latent_true_label",
    } <= set(label_ablation.get_column("label").to_list())


def test_employee_cycle_residual_diagnostic_helpers_return_issue_and_miss_views() -> (
    None
):
    config = PayrollConfig(
        facility_count=12,
        employee_count=180,
        pay_periods=12,
        employee_cycle_review_budget_percents=(0.05, 0.10),
    )
    payroll = generate_employee_pay_cycles(config).payroll
    scored = score_employee_pay_cycles(payroll, config).scored

    issue_type_metrics = employee_cycle_issue_type_model_performance(scored, 0.05)
    severe_misses = employee_cycle_severe_miss_examples(scored, 0.05, limit_per_model=2)

    assert issue_type_metrics.height > 0
    assert {
        "model",
        PayrollCol.ANOMALY_CATEGORY,
        MetricCol.RECALL_AT_K,
        MetricCol.RULE_MISSED_SEVERE_RECALL_AT_K,
        MetricCol.DOLLAR_CAPTURE_RATE,
    } <= set(issue_type_metrics.columns)
    assert severe_misses.height > 0
    assert {"model", PayrollCol.EMPLOYEE_PAY_CYCLE_ID, PayrollCol.Y_DOLLAR} <= set(
        severe_misses.columns,
    )


def test_employee_cycle_evaluation_supports_percent_review_budgets() -> None:
    config = PayrollConfig(
        facility_count=25,
        employee_count=120,
        pay_periods=10,
        employee_cycle_review_budget_percents=(0.05, 0.15, 0.30),
    )
    payroll = generate_employee_pay_cycles(config).payroll
    scored = score_employee_pay_cycles(payroll, config).scored

    evaluation = evaluate_employee_cycle_scores(scored, config)
    queue = build_employee_cycle_review_queue(
        scored,
        top_k=max(config.employee_cycle_review_budget_percents or (0.0,)),
    )

    assert evaluation.metrics.height == len(config.review_budgets)
    assert (
        evaluation.metrics.get_column(MetricCol.K)
        == pl.Series([0.05, 0.15, 0.30], dtype=pl.Float64)
    ).all()
    assert (evaluation.metrics.get_column(MetricCol.REVIEW_VOLUME) > 0).all()
    assert queue.height > 0


def test_employee_cycle_review_queue_uses_cycle_fields() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_employee_pay_cycles(config).payroll
    scored = score_employee_pay_cycles(payroll, config).scored

    queue = build_employee_cycle_review_queue(scored, top_k=10)

    assert queue.height > 0
    assert {
        PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
        PayrollCol.EMPLOYEE_ID,
        PayrollCol.FACILITY_ID,
        ReviewCol.PRIMARY_REASON,
        ReviewCol.EXPLANATION,
    } <= set(queue.columns)
    assert PayrollCol.SHIFT_DATE not in queue.columns
    assert PayrollCol.SHIFT_TYPE not in queue.columns


def test_employee_cycle_pipeline_runs_end_to_end() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))

    results = run_employee_cycle_pipeline(config)

    assert results.payroll.height > 0
    assert results.labels.height > 0
    assert results.scored.height == results.payroll.height
    assert results.validation_failures.height == 0
    assert results.metrics.height == len(config.review_budgets)
    assert results.model_comparison.height >= 4
    assert results.analyst_review_queue.height > 0
    assert results.evaluation_labeled_review_queue.height > 0
    assert results.facility_approval_summary.height > 0
    assert PayrollCol.EMPLOYEE_PAY_CYCLE_ID in results.analyst_review_queue.columns


def test_legacy_shift_pipeline_still_exposes_shift_level_artifacts() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))

    results = run_shift_level_pipeline(config)

    assert PayrollCol.SHIFT_ID in results.payroll.columns
    assert PayrollCol.PREMIUM_PAY in results.payroll.columns


def test_diagnostic_scenario_presets_reproducible_and_metadata_rich() -> None:
    config = PayrollConfig(employee_count=70, pay_periods=8, review_budgets=(5, 10))
    presets = diagnostic_scenario_presets()

    assert {
        "baseline",
        "rule-friendly",
        "statistical-friendly",
        "ml-friendly",
        "exposure-heavy",
        "subgroup-drift",
        "calendar-drift",
        "queue-stress",
    } <= set(presets)

    for name, scenario in presets.items():
        generated_a = generate_payroll(config, scenario=scenario)
        generated_b = generate_payroll(config, scenario=scenario)

        assert generated_a.payroll.equals(generated_b.payroll), name
        assert generated_a.labels.equals(generated_b.labels), name
        assert scenario.to_metadata()["name"] == name


def test_targeted_anomaly_controls_concentrate_configured_scope() -> None:
    config = PayrollConfig(employee_count=120, pay_periods=10, review_budgets=(5, 10))
    scenario = ScenarioSpec(
        name="targeted_operations",
        anomaly_plan=AnomalyPlan(
            target_count=35,
            targeted_controls=(
                TargetedAnomalyControl(
                    start_period=6,
                    subgroup_filters={PayrollCol.DEPARTMENT: "Nursing"},
                    category_weights={"overtime_spike": 1.0},
                    target_count=25,
                ),
            ),
        ),
    )

    payroll = generate_payroll(config, scenario=scenario).payroll
    target = payroll.filter(
        (pl.col(PayrollCol.DEPARTMENT) == "Nursing")
        & (pl.col(PayrollCol.PAY_PERIOD_INDEX) >= 6),
    )
    outside = payroll.filter(
        (pl.col(PayrollCol.DEPARTMENT) != "Nursing")
        | (pl.col(PayrollCol.PAY_PERIOD_INDEX) < 6),
    )

    target_rate = target.select(pl.mean(PayrollCol.IS_ANOMALY)).item()
    outside_rate = outside.select(pl.mean(PayrollCol.IS_ANOMALY)).item()

    assert target_rate > outside_rate


def test_drift_and_change_points_affect_only_configured_scope() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    baseline = generate_payroll(config).payroll
    scenario = ScenarioSpec(
        name="scoped_shift",
        drift_plans=(
            DriftPlan(
                start_period=6,
                subgroup_filters={PayrollCol.DEPARTMENT: "Nursing"},
                overtime_multiplier=1.5,
            ),
        ),
        change_points=(
            ChangePointEvent(
                name="gross_shift",
                start_period=7,
                subgroup_filters={PayrollCol.DEPARTMENT: "Nursing"},
                field=PayrollCol.GROSS_PAY,
                multiplier=1.2,
            ),
        ),
    )
    shifted = generate_payroll(config, scenario=scenario).payroll
    joined = baseline.select(
        PayrollCol.RECORD_ID,
        PayrollCol.DEPARTMENT,
        PayrollCol.PAY_PERIOD_INDEX,
        PayrollCol.OVERTIME_HOURS,
        PayrollCol.GROSS_PAY,
    ).join(
        shifted.select(
            PayrollCol.RECORD_ID,
            pl.col(PayrollCol.OVERTIME_HOURS).alias("shifted_overtime"),
            pl.col(PayrollCol.GROSS_PAY).alias("shifted_gross"),
        ),
        on=PayrollCol.RECORD_ID,
    )
    outside_scope = joined.filter(
        (pl.col(PayrollCol.DEPARTMENT) != "Nursing")
        | (pl.col(PayrollCol.PAY_PERIOD_INDEX) < 6),
    )

    assert outside_scope.select(
        (pl.col(PayrollCol.OVERTIME_HOURS) == pl.col("shifted_overtime")).all(),
    ).item()
    assert (
        joined.filter(
            (pl.col(PayrollCol.DEPARTMENT) == "Nursing")
            & (pl.col(PayrollCol.PAY_PERIOD_INDEX) >= 7)
            & (pl.col("shifted_gross") > pl.col(PayrollCol.GROSS_PAY)),
        ).height
        > 0
    )


def test_anomaly_mix_controls_and_label_separation() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scenario = ScenarioSpec(
        name="deduction_stress",
        anomaly_plan=AnomalyPlan(
            category_weights={"missing_deduction": 1.0},
            target_count=10,
        ),
    )
    generated = generate_payroll(config, scenario=scenario)
    results = run_pipeline(config, scenario=scenario)

    assert generated.labels.get_column(
        PayrollCol.ANOMALY_CATEGORY,
    ).unique().to_list() == [
        "missing_deduction",
    ]
    assert PayrollCol.IS_ANOMALY not in MODEL_FEATURE_COLUMNS
    assert PayrollCol.ANOMALY_DOLLARS not in MODEL_FEATURE_COLUMNS
    assert PayrollCol.IS_ANOMALY not in results.analyst_review_queue.columns
    assert results.scenario_metadata
    assert generated.payroll.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height == 10


def test_scenario_summary_and_component_regimes_differ() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scenarios = diagnostic_scenario_presets(("baseline", "rule-friendly"))
    summaries = []
    for name, scenario in scenarios.items():
        generated = generate_payroll(config, scenario=scenario)
        summaries.append(scenario_summary(generated.payroll, scenario=name))
    summary = pl.concat(summaries)
    unit_metrics = run_diagnostic_comparison_units(
        config,
        scenarios=scenarios,
        seeds=(42,),
        k=5,
    )
    superiority = pairwise_component_superiority(unit_metrics)

    assert {"overall", "category_mix", "subgroup_period"} & set(
        summary.get_column("scope").to_list(),
    )
    assert summary.get_column("scenario").n_unique() == 2
    assert superiority.height > 0
    assert {"mean_delta", "win_probability", "lower_95", "upper_95"} <= set(
        superiority.columns,
    )


def test_diagnostic_scenario_presets_produce_observable_contrast() -> None:
    config = PayrollConfig(employee_count=100, pay_periods=10, review_budgets=(5, 10))
    scenarios = diagnostic_scenario_presets(
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
    summaries = pl.concat(
        [
            scenario_sanity_summary(
                run_pipeline(config, scenario=scenario).scored,
                scenario=name,
                score_thresholds=(0.35, 0.45, 0.55),
            )
            for name, scenario in scenarios.items()
        ],
    )
    baseline = summaries.filter(pl.col("scenario") == "baseline").row(0, named=True)
    non_baseline = summaries.filter(pl.col("scenario") != "baseline")

    assert non_baseline.select(pl.max("score_p90")).item() != baseline["score_p90"]
    assert (
        non_baseline.select(pl.max("anomaly_dollars")).item()
        > baseline["anomaly_dollars"]
    )
    assert non_baseline.select(pl.max("max_subgroup_period_anomaly_share")).item() > 0
    assert (
        summaries.filter(pl.col("scenario") == "queue-stress")
        .select(
            pl.col("candidates_at_0.35"),
        )
        .item()
        > 0
    )


def test_scenario_sanity_summary_includes_sparse_condition_context() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scored = run_pipeline(
        config,
        scenario=diagnostic_scenario_presets(("queue-stress",))["queue-stress"],
    ).scored
    summary = scenario_sanity_summary(
        scored,
        scenario="queue-stress",
        score_thresholds=(0.35, 0.99),
    )

    assert {
        "scenario",
        "row_count",
        "anomaly_count",
        "anomaly_dollars",
        "score_p50",
        "score_p90",
        "candidates_at_0.35",
        "candidates_at_0.99",
        "category_mix",
        "max_subgroup_period_anomaly_share",
        "zero_threshold_candidates",
        "sparse_condition",
    } <= set(summary.columns)
    assert summary.select("zero_threshold_candidates").item() == "0.99"


def test_queue_simulation_output_shape_and_sanity() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scored = run_pipeline(config).scored
    simulation = simulate_queue_capacity(
        scored,
        QueueSimulationSpec(
            iterations=5,
            review_budget=5,
            fixed_capacity=3,
            capacity_sd=0,
            seed=7,
        ),
    )
    summary = summarize_queue_simulation(simulation)

    assert (
        simulation.height
        == scored.get_column(PayrollCol.PAY_PERIOD_INDEX).n_unique() * 5
    )
    assert {
        "overload",
        "missed_estimated_exposure",
        "missed_synthetic_anomaly_dollars",
    } <= set(simulation.columns)
    assert float(cast(Any, summary.get_column("overload_probability").min())) >= 0
    assert float(cast(Any, summary.get_column("avg_dollars_captured").min())) >= 0


def test_threshold_demand_queue_shape_and_capacity_shock_behavior() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scored = run_pipeline(
        config,
        scenario=diagnostic_scenario_presets(("queue-stress",))["queue-stress"],
    ).scored
    simulation = simulate_queue_capacity(
        scored,
        QueueSimulationSpec(
            iterations=3,
            review_budget=5,
            score_threshold=0.45,
            fixed_capacity=6,
            period_capacity_multipliers={8: 0.25, 9: 0.25},
            capacity_sd=0,
            seed=3,
            scenario="queue-stress",
        ),
    )
    summary = summarize_queue_simulation(simulation)

    assert {
        "scenario",
        "candidate_queue_size",
        "reviewed_records",
        "missed_estimated_exposure",
        "missed_synthetic_anomaly_dollars",
    } <= set(simulation.columns)
    assert simulation.get_column("demand_mode").unique().to_list() == [
        "score_threshold",
    ]
    assert (
        summary.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX).is_in([8, 9]))
        .select(
            pl.max("overload_probability"),
        )
        .item()
        > 0
    )


def test_threshold_grid_and_adaptive_queue_demand_outputs() -> None:
    config = PayrollConfig(employee_count=90, pay_periods=10, review_budgets=(5, 10))
    scored = run_pipeline(
        config,
        scenario=diagnostic_scenario_presets(("queue-stress",))["queue-stress"],
    ).scored
    grid = simulate_queue_capacity(
        scored,
        QueueSimulationSpec(
            iterations=2,
            review_budget=5,
            score_thresholds=(0.35, 0.45),
            fixed_capacity=4,
            capacity_sd=0,
            seed=11,
            scenario="queue-stress",
        ),
    )
    adaptive = simulate_queue_capacity(
        scored,
        QueueSimulationSpec(
            iterations=2,
            review_budget=5,
            adaptive_threshold_quantile=0.90,
            fixed_capacity=4,
            capacity_sd=0,
            seed=11,
            scenario="queue-stress",
        ),
    )
    grid_summary = summarize_queue_simulation(grid)
    adaptive_summary = summarize_queue_simulation(adaptive)

    assert set(grid.get_column("demand_mode")) == {"threshold_grid"}
    assert grid.get_column("resolved_threshold").n_unique() == 2
    assert adaptive.get_column("demand_mode").unique().to_list() == [
        "adaptive_threshold",
    ]
    assert adaptive.select(pl.col("resolved_threshold").is_not_null().all()).item()
    assert grid.select(pl.max("candidate_queue_size")).item() > 0
    assert {
        "scenario",
        "resolved_threshold",
        "demand_mode",
        "avg_candidate_queue_size",
        "avg_reviewed_records",
        "overload_probability",
        "avg_missed_estimated_exposure",
        "avg_missed_synthetic_anomaly_dollars",
    } <= set(grid_summary.columns)
    assert "adaptive_threshold_quantile" in adaptive_summary.columns


def test_statistical_diagnostics_output_schemas_non_empty() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scored = run_pipeline(config).scored

    intervals = review_budget_interval_summary(scored, k=5, samples=10, seed=1)
    subgroups = subgroup_diagnostics(scored, k=5)
    calibration = expected_pay_calibration(scored, by=PayrollCol.DEPARTMENT)

    assert intervals.height == 4
    assert {"metric", "lower_95", "upper_95", "scope"} <= set(intervals.columns)
    assert subgroups.height > 0
    assert {"raw_anomaly_rate", "pooled_anomaly_rate", "shrinkage"} <= set(
        subgroups.columns,
    )
    assert calibration.height > 0
    assert {"coverage", "avg_interval_width", "avg_residual"} <= set(
        calibration.columns,
    )


def test_plot_helper_input_tables_include_rich_context_columns() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scenarios = diagnostic_scenario_presets(("baseline", "subgroup-drift"))
    unit_metrics = run_diagnostic_comparison_units(
        config,
        scenarios=scenarios,
        seeds=(42,),
        k=5,
    )
    superiority = pairwise_component_superiority(unit_metrics)
    scored = run_pipeline(config, scenario=scenarios["subgroup-drift"]).scored
    subgroups = subgroup_diagnostics(scored, k=5, scenario="subgroup-drift")
    top_subgroups = top_subgroup_diagnostics(subgroups, top_n=6)
    calibration = calibration_plot_inputs(scored, by=PayrollCol.DEPARTMENT)

    assert {"scenario", "samples", "mean_delta", "lower_95", "upper_95"} <= set(
        superiority.columns,
    )
    assert {"records", "anomaly_count", "lower_95", "upper_95", "scenario"} <= set(
        top_subgroups.columns,
    )
    assert top_subgroups.height >= 6
    assert {"subgroup", "residual", "interval_width", "tail_excess"} <= set(
        calibration.columns,
    )
    assert calibration.height >= 2


def test_threshold_scoring_emits_facility_variance_and_manual_pack_flags() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scored = score_payroll(
        add_rule_flags(build_features(generate_payroll(config).payroll)),
        config,
    )

    assert {
        ScoreCol.THRESHOLD_FACILITY_VARIANCE_FLAG,
        ScoreCol.THRESHOLD_MANUAL_PACK_FLAG,
    } <= set(scored.columns)
    assert scored.select(pl.sum(ScoreCol.THRESHOLD_FACILITY_VARIANCE_FLAG)).item() >= 0


def test_threshold_baseline_metrics_include_manual_pack_and_burden_columns() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scored = score_payroll(
        add_rule_flags(build_features(generate_payroll(config).payroll)),
        config,
    )
    threshold_metrics = evaluate_scores(scored, config).threshold_baseline_metrics

    assert {
        "manual_threshold_pack",
        "facility_payroll_variance_threshold",
    } <= set(threshold_metrics.get_column("baseline").to_list())
    assert {
        MetricCol.NATIVE_REVIEW_BURDEN,
        MetricCol.EXPOSURE_PER_REVIEW,
        MetricCol.MISSED_ESTIMATED_EXPOSURE,
    } <= set(threshold_metrics.columns)


def test_business_proof_diagnostics_emit_plot_ready_tables() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scenarios = diagnostic_scenario_presets(
        ("baseline", "overtime-staffing-pressure", "premium-mismatch"),
    )
    ranking_units = business_proof_ranking_units(
        config,
        scenarios=scenarios,
        seeds=(42,),
        review_budgets=(5,),
    )
    threshold_units = business_proof_threshold_units(
        config,
        scenarios=scenarios,
        seeds=(42,),
    )
    intervals = business_proof_metric_intervals(
        ranking_units,
        metric_columns=(MetricCol.EXPOSURE_PER_REVIEW,),
        group_columns=("scenario", "method", MetricCol.K),
    )
    win_rates = business_proof_hybrid_win_rates(
        ranking_units,
        metric=MetricCol.EXPOSURE_PER_REVIEW,
    )

    assert ranking_units.height > 0
    assert threshold_units.height > 0
    assert {"method", "method_type", MetricCol.EXPOSURE_PER_REVIEW} <= set(
        ranking_units.columns,
    )
    assert {"method", MetricCol.NATIVE_REVIEW_BURDEN} <= set(threshold_units.columns)
    assert {"mean", "lower_95", "upper_95", "samples"} <= set(intervals.columns)
    assert {"comparator", "win_probability", "mean_delta", "samples"} <= set(
        win_rates.columns,
    )


def test_legacy_notebooks_are_valid_python() -> None:
    legacy_notebooks = [
        Path("notebooks/legacy/shift_level/06_internal_statistical_diagnostics.py"),
        Path("notebooks/legacy/shift_level/07_simulation_and_stress_testing.py"),
        Path("notebooks/legacy/shift_level/08_snf_payroll_approval_case_studies.py"),
    ]
    for path in legacy_notebooks:
        source = path.read_text()
        compile(source, str(path), "exec")


def _load_notebook_module(module_path: Path) -> Any:
    notebooks_dir = str(Path("notebooks").resolve())
    if notebooks_dir not in sys.path:
        sys.path.insert(0, notebooks_dir)
    spec = importlib.util.spec_from_file_location(
        module_path.stem,
        module_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_notebook_display_helper_is_callable() -> None:
    display_module = _load_notebook_module(Path("notebooks/common/display.py"))
    assert callable(display_module.setup_notebook_html)
    assert callable(display_module.setup_polars_display)
    display_module.setup_polars_display()


def test_notebook_execution_helper_respects_validation_env_var() -> None:
    execution_module = _load_notebook_module(Path("notebooks/common/execution.py"))
    assert callable(execution_module.notebook_validation_mode)

    os.environ["NOTEBOOK_VALIDATE"] = "1"
    try:
        assert execution_module.notebook_validation_mode() is True
    finally:
        del os.environ["NOTEBOOK_VALIDATE"]

    assert execution_module.notebook_validation_mode() is False


def test_core_package_modules_compile_cleanly() -> None:
    assert importlib.util.find_spec("payroll_anomaly_ranking.charts") is None
    for path in Path("src/payroll_anomaly_ranking").glob("*.py"):
        source = path.read_text()
        compile(source, str(path), "exec")


def test_checked_ggplot_allows_valid_render() -> None:
    plots = _load_notebook_plots_module()
    plot = (
        plots.ggplot({"x": [1, 2], "y": [1, 2]}, plots.aes("x", "y"))
        + plots.geom_point()
    )

    html = plot._repr_html_()

    assert "__error_message" not in html


def test_checked_ggplot_raises_on_embedded_render_error() -> None:
    plots = _load_notebook_plots_module()
    plot = (
        plots.ggplot({"x": [1, 2], "y": [1, 2]}, plots.aes("x", "y"))
        + plots.geom_point()
        + plots.geom_vline(xintercept=(7.5, 11.5))
    )

    with pytest.raises(plots.LetsPlotRenderError, match="Can't convert to number"):
        plot._repr_html_()


def test_scoring_excludes_injected_evaluation_truth() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_payroll(config).payroll
    ruled = add_rule_flags(build_features(payroll))

    assert PayrollCol.IS_ANOMALY not in MODEL_FEATURE_COLUMNS
    assert PayrollCol.ANOMALY_CATEGORY not in MODEL_FEATURE_COLUMNS
    assert PayrollCol.ANOMALY_DOLLARS not in MODEL_FEATURE_COLUMNS
    assert PayrollCol.OOD_PAY_CODE_CONTEXT not in MODEL_FEATURE_COLUMNS
    assert PayrollCol.PAY_CODE not in MODEL_FEATURE_COLUMNS
    assert _feature_matrix(ruled).shape[1] == len(MODEL_FEATURE_COLUMNS)

    scored = score_payroll(ruled, config)
    relabeled = ruled.with_columns(
        pl.lit(1).alias(PayrollCol.IS_ANOMALY),
        pl.lit("changed_label").alias(PayrollCol.ANOMALY_CATEGORY),
        (pl.col(PayrollCol.ANOMALY_DOLLARS) + 999_999).alias(
            PayrollCol.ANOMALY_DOLLARS,
        ),
    )
    relabeled_scored = score_payroll(relabeled, config)

    assert scored.select(
        ScoreCol.ESTIMATED_EXPOSURE,
        ScoreCol.EXPOSURE_SCORE,
        ScoreCol.FINAL_ANOMALY_SCORE,
        ScoreCol.COMPOSITE_UNCERTAINTY_SCORE,
    ).equals(
        relabeled_scored.select(
            ScoreCol.ESTIMATED_EXPOSURE,
            ScoreCol.EXPOSURE_SCORE,
            ScoreCol.FINAL_ANOMALY_SCORE,
            ScoreCol.COMPOSITE_UNCERTAINTY_SCORE,
        ),
    )


def test_employee_cycle_scoring_excludes_evaluation_labels_from_features() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_employee_pay_cycles(config).payroll
    results = score_employee_pay_cycles(payroll, config)

    assert PayrollCol.IS_ANOMALY not in results.feature_columns
    assert PayrollCol.ANOMALY_CATEGORY not in results.feature_columns
    assert PayrollCol.ANOMALY_DOLLARS not in results.feature_columns
    assert PayrollCol.Y_ISSUE not in results.feature_columns
    assert PayrollCol.Y_DOLLAR not in results.feature_columns
    assert PayrollCol.SEVERE_ISSUE not in results.feature_columns
    assert PayrollCol.RULE_MISSED_SEVERE_ISSUE not in results.feature_columns
    assert PayrollCol.RELEVANCE_GRADE not in results.feature_columns
    assert PayrollCol.NET_UTILITY not in results.feature_columns


def test_period_safe_feature_references_and_early_fallbacks() -> None:
    payroll = pl.DataFrame(
        {
            PayrollCol.RECORD_ID: [0, 1, 2, 3, 4],
            PayrollCol.EMPLOYEE_ID: ["a", "b", "a", "b", "c"],
            PayrollCol.PAY_PERIOD_INDEX: [1, 1, 2, 2, 3],
            PayrollCol.DEPARTMENT: ["Nursing"] * 5,
            PayrollCol.JOB_FAMILY: ["CNA"] * 5,
            PayrollCol.LOCATION: ["SNF-F001"] * 5,
            PayrollCol.PAY_TYPE: ["hourly"] * 5,
            PayrollCol.PAY_CODE: ["SNF_REG"] * 5,
            PayrollCol.TENURE_MONTHS: [12] * 5,
            PayrollCol.GROSS_PAY: [1000.0, 3000.0, 2000.0, 4000.0, 5000.0],
            PayrollCol.DEDUCTIONS: [200.0, 600.0, 400.0, 800.0, 1000.0],
            PayrollCol.NET_PAY: [800.0, 2400.0, 1600.0, 3200.0, 4000.0],
            PayrollCol.OVERTIME_HOURS: [0.0, 0.0, 2.0, 4.0, 8.0],
        },
    )

    featured = build_features(payroll).sort(PayrollCol.RECORD_ID)

    assert featured.row(0, named=True)["gross_pay_rolling_median"] is None
    assert featured.row(0, named=True)[FeatureCol.PRIOR_EMPLOYEE_PAY_PERIOD_COUNT] == 0
    assert featured.row(2, named=True)[FeatureCol.PRIOR_EMPLOYEE_PAY_PERIOD_COUNT] == 1
    assert featured.row(2, named=True)["gross_pay_rolling_median"] == 1000.0
    assert featured.row(0, named=True)["peer_gross_median"] == 1000.0
    assert featured.row(2, named=True)["peer_gross_median"] == 2000.0
    assert featured.row(2, named=True)["gross_pay_percentile"] == 0.5
    assert featured.row(0, named=True)["gross_pay_robust_z"] is not None


def test_missing_deduction_rule_and_explanation() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_payroll(config).payroll
    latest_period = payroll.select(pl.max(PayrollCol.PAY_PERIOD_INDEX)).item()
    missing_record_id = payroll.filter(
        (pl.col(PayrollCol.PAY_PERIOD_INDEX) == latest_period)
        & (pl.col(PayrollCol.GROSS_PAY) > 0),
    ).get_column(PayrollCol.RECORD_ID)[0]
    payroll = payroll.with_columns(
        pl.when(pl.col(PayrollCol.RECORD_ID) == missing_record_id)
        .then(0.0)
        .otherwise(pl.col(PayrollCol.DEDUCTIONS))
        .alias(PayrollCol.DEDUCTIONS),
    )

    scored = score_payroll(add_rule_flags(build_features(payroll)), config)
    row = scored.filter(pl.col(PayrollCol.RECORD_ID) == missing_record_id).row(
        0,
        named=True,
    )
    queue = build_review_queue(
        scored.with_columns(pl.lit(1).alias(ScoreCol.PAY_PERIOD_RANK)),
        top_k=1,
    )
    queue_row = queue.filter(
        pl.col(PayrollCol.EMPLOYEE_ID) == row[PayrollCol.EMPLOYEE_ID],
    ).row(0, named=True)

    assert row[RuleCol.MISSING_DEDUCTION] == 1
    assert "missing_deduction" in row[RuleCol.REASON_CODES]
    assert row[RuleCol.SEVERITY_SCORE] >= 18
    assert (
        "deductions" in queue_row["primary_reason"]
        or "deductions" in queue_row["explanation"]
    )


def test_review_queue_field_separation_sort_order_and_safe_language() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_payroll(config).payroll
    scored = score_payroll(add_rule_flags(build_features(payroll)), config)

    analyst_queue = build_review_queue(scored, top_k=10)
    evaluation_queue = build_evaluation_review_queue(scored, top_k=10)

    leaked = {
        PayrollCol.IS_ANOMALY,
        PayrollCol.ANOMALY_CATEGORY,
        PayrollCol.ANOMALY_DOLLARS,
    }
    assert not leaked & set(analyst_queue.columns)
    assert PayrollCol.OOD_PAY_CODE_CONTEXT not in analyst_queue.columns
    assert leaked <= set(evaluation_queue.columns)
    assert analyst_queue.get_column(PayrollCol.PAY_PERIOD_INDEX).n_unique() == 1
    assert (
        analyst_queue.get_column(PayrollCol.PAY_PERIOD_INDEX)[0]
        == scored.select(
            pl.max(PayrollCol.PAY_PERIOD_INDEX),
        ).item()
    )
    assert analyst_queue.select(PayrollCol.PAY_PERIOD_INDEX, "rank").equals(
        analyst_queue.sort("rank").select(
            PayrollCol.PAY_PERIOD_INDEX,
            "rank",
        ),
    )
    assert (
        not analyst_queue.get_column("explanation")
        .str.contains("confirmed fraud|confirmed misconduct|known synthetic anomaly")
        .any()
    )


def test_rolling_origin_validation_stability_and_leakage_checks() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll = generate_payroll(config).payroll
    scored = score_payroll(add_rule_flags(build_features(payroll)), config)
    rolling = rolling_origin_evaluation(scored, config)
    analyst_queue = build_review_queue(scored, top_k=10)
    checks = leakage_checks(analyst_queue)

    assert rolling.metrics.height > 0
    assert (
        rolling.metrics.get_column("train_end_period")
        < rolling.metrics.get_column("validation_period")
    ).all()
    assert (
        rolling.metrics.get_column("validation_period")
        < rolling.metrics.get_column("test_period")
    ).all()
    assert (
        rolling.selected_settings.select("selected_threshold").height
        == rolling.metrics.height
    )
    assert (
        rolling.stability_summary.row(0, named=True)["origin_count"]
        == rolling.metrics.height
    )
    assert {
        MetricCol.REVIEW_VOLUME,
        MetricCol.EXPOSURE_PER_REVIEW,
        MetricCol.DOLLARS_CAPTURED_AT_K,
        MetricCol.DOLLAR_CAPTURE_RATE,
    } <= set(rolling.metrics.columns)
    assert (
        rolling.metrics.get_column(MetricCol.REVIEW_VOLUME) > config.review_budgets[0]
    ).all()
    assert (rolling.metrics.get_column(MetricCol.EXPOSURE_PER_REVIEW) >= 0).all()
    assert (rolling.metrics.get_column(MetricCol.DOLLAR_CAPTURE_RATE) >= 0).all()
    assert (rolling.metrics.get_column(MetricCol.DOLLAR_CAPTURE_RATE) <= 1).all()
    assert checks.get_column("passed").all()


def test_pay_code_generation_and_late_period_ood_drift() -> None:
    config = PayrollConfig(employee_count=120, pay_periods=12, review_budgets=(5, 10))
    payroll = generate_payroll(config).payroll
    late_start = config.pay_periods - 3

    assert PayrollCol.PAY_CODE in payroll.columns
    assert PayrollCol.OOD_PAY_CODE_CONTEXT in payroll.columns
    assert payroll.get_column(PayrollCol.PAY_CODE).null_count() == 0
    assert (
        payroll.filter(
            (pl.col(PayrollCol.PAY_PERIOD_INDEX) >= late_start)
            & (
                pl.col(PayrollCol.OOD_PAY_CODE_CONTEXT)
                == "late_period_new_or_rare_pay_code"
            ),
        ).height
        > 0
    )


def test_uncertainty_outputs_intervals_and_conformal_context() -> None:
    config = PayrollConfig(employee_count=120, pay_periods=12, review_budgets=(5, 10))
    scored = score_payroll(
        add_rule_flags(build_features(generate_payroll(config).payroll)),
        config,
    )
    late = scored.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) == config.pay_periods)

    required = {
        ScoreCol.ENSEMBLE_DISAGREEMENT_UNCERTAINTY,
        ScoreCol.BOOTSTRAP_INTERVAL_UNCERTAINTY,
        ScoreCol.CONFORMAL_P_VALUE,
        ScoreCol.CONFORMAL_PERCENTILE,
        ScoreCol.EXPECTED_GROSS_PAY_P10,
        ScoreCol.EXPECTED_GROSS_PAY_P50,
        ScoreCol.EXPECTED_GROSS_PAY_P90,
        ScoreCol.EXPECTED_GROSS_PAY_INTERVAL_WIDTH,
        ScoreCol.GROSS_PAY_EXCESS_VS_P90,
        ScoreCol.COMPOSITE_UNCERTAINTY_SCORE,
        ReviewCol.UNCERTAINTY_BUCKET,
        ReviewCol.PRIMARY_UNCERTAINTY_REASON,
    }
    assert required <= set(scored.columns)
    assert late.select(ScoreCol.EXPECTED_GROSS_PAY_P90).drop_nulls().height > 0
    assert (
        scored.select(ReviewCol.UNCERTAINTY_BUCKET).drop_nulls().height == scored.height
    )

    relabeled = scored.with_columns(
        pl.lit(0.0).alias(ScoreCol.CONFORMAL_P_VALUE),
        pl.lit(0.0).alias(ScoreCol.CONFORMAL_PERCENTILE),
    )
    assert scored.select(ScoreCol.COMPOSITE_UNCERTAINTY_SCORE).equals(
        relabeled.select(ScoreCol.COMPOSITE_UNCERTAINTY_SCORE),
    )
