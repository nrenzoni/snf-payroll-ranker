import polars as pl

from payroll_anomaly_ranking.columns import MODEL_FEATURE_COLUMNS, OutputName, PayrollCol, RuleCol, ScoreCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import generate_payroll
from payroll_anomaly_ranking.evaluation import evaluate_scores, leakage_checks, rolling_origin_evaluation
from payroll_anomaly_ranking.explainability import build_evaluation_review_queue, build_review_queue
from payroll_anomaly_ranking.features import build_features
from payroll_anomaly_ranking.models import _feature_matrix, score_payroll
from payroll_anomaly_ranking.pipeline import run_pipeline
from payroll_anomaly_ranking.rules import add_rule_flags
from payroll_anomaly_ranking.validation import validate_payroll


def test_end_to_end_smoke() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll, labels = generate_payroll(config)
    failures, warnings = validate_payroll(payroll)
    featured = build_features(payroll)
    ruled = add_rule_flags(featured)
    scored = score_payroll(ruled, config)
    metrics, comparison, category = evaluate_scores(scored, config)
    queue = build_review_queue(scored, top_k=10)

    assert payroll.height > 0
    assert labels.height > 0
    assert failures.height == 0
    assert warnings.height >= 0
    assert "final_anomaly_score" in scored.columns
    assert metrics.height == 2
    assert comparison.height == 4
    assert category.height > 0
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
    assert (config.output_dir / "evaluation" / "rolling_origin_metrics.csv").exists()
    assert (config.output_dir / "evaluation" / "validation_selected_settings.csv").exists()
    assert (config.output_dir / "evaluation" / "stability_summary.csv").exists()
    assert (config.output_dir / "evaluation" / "leakage_checks.csv").exists()
    assert (config.output_dir / "evaluation" / OutputName.ANALYST_REVIEW_QUEUE).exists()
    assert (config.output_dir / "evaluation" / OutputName.EVALUATION_LABELED_REVIEW_QUEUE).exists()


def test_scoring_excludes_injected_evaluation_truth() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll, _ = generate_payroll(config)
    ruled = add_rule_flags(build_features(payroll))

    assert PayrollCol.IS_ANOMALY not in MODEL_FEATURE_COLUMNS
    assert PayrollCol.ANOMALY_CATEGORY not in MODEL_FEATURE_COLUMNS
    assert PayrollCol.ANOMALY_DOLLARS not in MODEL_FEATURE_COLUMNS
    assert _feature_matrix(ruled).shape[1] == len(MODEL_FEATURE_COLUMNS)

    scored = score_payroll(ruled, config)
    relabeled = ruled.with_columns(
        pl.lit(1).alias(PayrollCol.IS_ANOMALY),
        pl.lit("changed_label").alias(PayrollCol.ANOMALY_CATEGORY),
        (pl.col(PayrollCol.ANOMALY_DOLLARS) + 999_999).alias(PayrollCol.ANOMALY_DOLLARS),
    )
    relabeled_scored = score_payroll(relabeled, config)

    assert scored.select(ScoreCol.ESTIMATED_EXPOSURE, ScoreCol.EXPOSURE_SCORE, ScoreCol.FINAL_ANOMALY_SCORE).equals(
        relabeled_scored.select(ScoreCol.ESTIMATED_EXPOSURE, ScoreCol.EXPOSURE_SCORE, ScoreCol.FINAL_ANOMALY_SCORE)
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
            PayrollCol.TENURE_MONTHS: [12] * 5,
            PayrollCol.GROSS_PAY: [1000.0, 3000.0, 2000.0, 4000.0, 5000.0],
            PayrollCol.DEDUCTIONS: [200.0, 600.0, 400.0, 800.0, 1000.0],
            PayrollCol.NET_PAY: [800.0, 2400.0, 1600.0, 3200.0, 4000.0],
            PayrollCol.OVERTIME_HOURS: [0.0, 0.0, 2.0, 4.0, 8.0],
        }
    )

    featured = build_features(payroll).sort(PayrollCol.RECORD_ID)

    assert featured.row(0, named=True)["gross_pay_rolling_median"] is None
    assert featured.row(2, named=True)["gross_pay_rolling_median"] == 1000.0
    assert featured.row(0, named=True)["peer_gross_median"] == 1000.0
    assert featured.row(2, named=True)["peer_gross_median"] == 2000.0
    assert featured.row(2, named=True)["gross_pay_percentile"] == 0.5
    assert featured.row(0, named=True)["gross_pay_robust_z"] is not None


def test_missing_deduction_rule_and_explanation() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll, _ = generate_payroll(config)
    missing_record_id = payroll.filter(pl.col(PayrollCol.GROSS_PAY) > 0).get_column(PayrollCol.RECORD_ID)[0]
    payroll = payroll.with_columns(
        pl.when(pl.col(PayrollCol.RECORD_ID) == missing_record_id)
        .then(0.0)
        .otherwise(pl.col(PayrollCol.DEDUCTIONS))
        .alias(PayrollCol.DEDUCTIONS)
    )

    scored = score_payroll(add_rule_flags(build_features(payroll)), config)
    row = scored.filter(pl.col(PayrollCol.RECORD_ID) == missing_record_id).row(0, named=True)
    queue = build_review_queue(scored.with_columns(pl.lit(1).alias(ScoreCol.PAY_PERIOD_RANK)), top_k=1)
    queue_row = queue.filter(pl.col(PayrollCol.EMPLOYEE_ID) == row[PayrollCol.EMPLOYEE_ID]).row(0, named=True)

    assert row[RuleCol.MISSING_DEDUCTION] == 1
    assert "missing_deduction" in row[RuleCol.REASON_CODES]
    assert row[RuleCol.SEVERITY_SCORE] >= 18
    assert "deductions" in queue_row["primary_reason"] or "deductions" in queue_row["explanation"]


def test_review_queue_field_separation_sort_order_and_safe_language() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll, _ = generate_payroll(config)
    scored = score_payroll(add_rule_flags(build_features(payroll)), config)

    analyst_queue = build_review_queue(scored, top_k=10)
    evaluation_queue = build_evaluation_review_queue(scored, top_k=10)

    leaked = {PayrollCol.IS_ANOMALY, PayrollCol.ANOMALY_CATEGORY, PayrollCol.ANOMALY_DOLLARS}
    assert not leaked & set(analyst_queue.columns)
    assert leaked <= set(evaluation_queue.columns)
    assert analyst_queue.select(PayrollCol.PAY_PERIOD_INDEX, "rank").equals(
        analyst_queue.sort([PayrollCol.PAY_PERIOD_INDEX, "rank"]).select(PayrollCol.PAY_PERIOD_INDEX, "rank")
    )
    assert not analyst_queue.get_column("explanation").str.contains("confirmed fraud|confirmed misconduct|known synthetic anomaly").any()


def test_rolling_origin_validation_stability_and_leakage_checks() -> None:
    config = PayrollConfig(employee_count=80, pay_periods=10, review_budgets=(5, 10))
    payroll, _ = generate_payroll(config)
    scored = score_payroll(add_rule_flags(build_features(payroll)), config)
    rolling_metrics, settings, stability = rolling_origin_evaluation(scored, config)
    analyst_queue = build_review_queue(scored, top_k=10)
    checks = leakage_checks(analyst_queue)

    assert rolling_metrics.height > 0
    assert (rolling_metrics.get_column("train_end_period") < rolling_metrics.get_column("validation_period")).all()
    assert (rolling_metrics.get_column("validation_period") < rolling_metrics.get_column("test_period")).all()
    assert settings.select("selected_threshold").height == rolling_metrics.height
    assert stability.row(0, named=True)["origin_count"] == rolling_metrics.height
    assert checks.get_column("passed").all()
