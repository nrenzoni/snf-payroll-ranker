from pathlib import Path

import polars as pl

from payroll_anomaly_ranking.columns import (
    MODEL_FEATURE_COLUMNS,
    FeatureCol,
    OutputName,
    PayrollCol,
    ReviewCol,
    RuleCol,
    ScoreCol,
)
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import generate_payroll
from payroll_anomaly_ranking.diagnostics import (
    expected_pay_calibration,
    review_budget_interval_summary,
    subgroup_diagnostics,
)
from payroll_anomaly_ranking.evaluation import (
    evaluate_scores,
    leakage_checks,
    rolling_origin_evaluation,
)
from payroll_anomaly_ranking.explainability import (
    build_evaluation_review_queue,
    build_review_queue,
)
from payroll_anomaly_ranking.features import build_features
from payroll_anomaly_ranking.models import _feature_matrix, score_payroll
from payroll_anomaly_ranking.pipeline import run_pipeline
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
)
from payroll_anomaly_ranking.validation import validate_payroll


def test_end_to_end_smoke() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll, labels = generate_payroll(config)
    failures, warnings = validate_payroll(payroll)
    featured = build_features(payroll)
    ruled = add_rule_flags(featured)
    scored = score_payroll(ruled, config)
    metrics, comparison, category, uncertainty, risk_coverage, interval = (
        evaluate_scores(
            scored,
            config,
        )
    )
    queue = build_review_queue(scored, top_k=10)

    assert payroll.height > 0
    assert labels.height > 0
    assert failures.height == 0
    assert warnings.height >= 0
    assert "final_anomaly_score" in scored.columns
    assert metrics.height == 2
    assert comparison.height == 4
    assert category.height > 0
    assert uncertainty.height > 0
    assert risk_coverage.height > 0
    assert interval.height == 1
    assert queue.height > 0
    assert not {"name", "email", "bank_account", "ssn"} & set(payroll.columns)


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


def test_default_payroll_generation_reproducible_and_schema_compatible() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))

    payroll_a, labels_a = generate_payroll(config)
    payroll_b, labels_b = generate_payroll(config)
    failures, _ = validate_payroll(payroll_a)

    assert payroll_a.equals(payroll_b)
    assert labels_a.equals(labels_b)
    assert failures.height == 0
    assert {
        PayrollCol.IS_ANOMALY,
        PayrollCol.ANOMALY_CATEGORY,
        PayrollCol.ANOMALY_DOLLARS,
    } <= set(payroll_a.columns)


def test_scenario_generation_is_reproducible_with_same_seed() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scenario = ScenarioSpec(
        name="mix_shift",
        anomaly_plan=AnomalyPlan(
            category_weights={"overtime_spike": 1.0},
            target_count=12,
        ),
    )

    payroll_a, labels_a = generate_payroll(config, scenario=scenario)
    payroll_b, labels_b = generate_payroll(config, scenario=scenario)

    assert payroll_a.equals(payroll_b)
    assert labels_a.equals(labels_b)
    assert labels_a.get_column(PayrollCol.ANOMALY_CATEGORY).unique().to_list() == [
        "overtime_spike",
    ]


def test_drift_and_change_points_affect_only_configured_scope() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    baseline, _ = generate_payroll(config)
    scenario = ScenarioSpec(
        name="scoped_shift",
        drift_plans=(
            DriftPlan(
                start_period=6,
                subgroup_filters={PayrollCol.DEPARTMENT: "Operations"},
                overtime_multiplier=1.5,
            ),
        ),
        change_points=(
            ChangePointEvent(
                name="gross_shift",
                start_period=7,
                subgroup_filters={PayrollCol.DEPARTMENT: "Operations"},
                field=PayrollCol.GROSS_PAY,
                multiplier=1.2,
            ),
        ),
    )
    shifted, _ = generate_payroll(config, scenario=scenario)
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
        (pl.col(PayrollCol.DEPARTMENT) != "Operations")
        | (pl.col(PayrollCol.PAY_PERIOD_INDEX) < 6),
    )

    assert outside_scope.select(
        (pl.col(PayrollCol.OVERTIME_HOURS) == pl.col("shifted_overtime")).all(),
    ).item()
    assert (
        joined.filter(
            (pl.col(PayrollCol.DEPARTMENT) == "Operations")
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
    payroll, labels = generate_payroll(config, scenario=scenario)
    results = run_pipeline(config, scenario=scenario)

    assert labels.get_column(PayrollCol.ANOMALY_CATEGORY).unique().to_list() == [
        "missing_deduction",
    ]
    assert PayrollCol.IS_ANOMALY not in MODEL_FEATURE_COLUMNS
    assert PayrollCol.ANOMALY_DOLLARS not in MODEL_FEATURE_COLUMNS
    assert PayrollCol.IS_ANOMALY not in results["analyst_review_queue"].columns
    assert "scenario_metadata" in results
    assert payroll.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height == 10


def test_queue_simulation_output_shape_and_sanity() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scored = run_pipeline(config)["scored"]
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
    assert summary.get_column("overload_probability").min() >= 0
    assert summary.get_column("avg_dollars_captured").min() >= 0


def test_statistical_diagnostics_output_schemas_non_empty() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    scored = run_pipeline(config)["scored"]

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


def test_internal_notebooks_have_bounded_reproducibility_defaults() -> None:
    notebook_06 = Path("notebooks/06_internal_statistical_diagnostics.py").read_text()
    notebook_07 = Path("notebooks/07_simulation_and_stress_testing.py").read_text()

    assert "LetsPlot.setup_html()" in notebook_06
    assert "LetsPlot.setup_html()" in notebook_07
    assert "samples=50" in notebook_06
    assert "iterations=40" in notebook_07


def test_scoring_excludes_injected_evaluation_truth() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll, _ = generate_payroll(config)
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


def test_period_safe_feature_references_and_early_fallbacks() -> None:
    payroll = pl.DataFrame(
        {
            PayrollCol.RECORD_ID: [0, 1, 2, 3, 4],
            PayrollCol.EMPLOYEE_ID: ["a", "b", "a", "b", "c"],
            PayrollCol.PAY_PERIOD_INDEX: [1, 1, 2, 2, 3],
            PayrollCol.DEPARTMENT: ["Finance"] * 5,
            PayrollCol.JOB_FAMILY: ["Payroll"] * 5,
            PayrollCol.LOCATION: ["Remote"] * 5,
            PayrollCol.PAY_TYPE: ["salaried"] * 5,
            PayrollCol.PAY_CODE: ["SAL"] * 5,
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
    payroll, _ = generate_payroll(config)
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
    payroll, _ = generate_payroll(config)
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
    payroll, _ = generate_payroll(config)
    scored = score_payroll(add_rule_flags(build_features(payroll)), config)
    rolling_metrics, settings, stability = rolling_origin_evaluation(scored, config)
    analyst_queue = build_review_queue(scored, top_k=10)
    checks = leakage_checks(analyst_queue)

    assert rolling_metrics.height > 0
    assert (
        rolling_metrics.get_column("train_end_period")
        < rolling_metrics.get_column("validation_period")
    ).all()
    assert (
        rolling_metrics.get_column("validation_period")
        < rolling_metrics.get_column("test_period")
    ).all()
    assert settings.select("selected_threshold").height == rolling_metrics.height
    assert stability.row(0, named=True)["origin_count"] == rolling_metrics.height
    assert checks.get_column("passed").all()


def test_pay_code_generation_and_late_period_ood_drift() -> None:
    config = PayrollConfig(employee_count=120, pay_periods=12, review_budgets=(5, 10))
    payroll, _ = generate_payroll(config)
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
        add_rule_flags(build_features(generate_payroll(config)[0])),
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
