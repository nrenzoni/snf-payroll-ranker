from __future__ import annotations

from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.columns import PayrollCol
from payroll_anomaly_ranking.data import generate_payroll
from payroll_anomaly_ranking.evaluation import backtest_by_period, evaluate_scores
from payroll_anomaly_ranking.explainability import build_review_queue
from payroll_anomaly_ranking.features import build_features
from payroll_anomaly_ranking.models import score_payroll
from payroll_anomaly_ranking.rules import add_rule_flags
from payroll_anomaly_ranking.validation import payroll_aggregations, validate_payroll


def run_pipeline(config: PayrollConfig = PayrollConfig(), *, write_outputs: bool = False) -> dict[str, object]:
    payroll, labels = generate_payroll(config)
    failures, warnings = validate_payroll(payroll)
    features = build_features(payroll)
    ruled = add_rule_flags(features)
    scored = score_payroll(ruled, config)
    metrics, comparison, category = evaluate_scores(scored, config)
    category = category.sort(PayrollCol.ANOMALY_CATEGORY)
    backtest = backtest_by_period(scored, config)
    queue = build_review_queue(scored, top_k=max(config.review_budgets))
    results = {
        "payroll": payroll,
        "labels": labels,
        "validation_failures": failures,
        "validation_warnings": warnings,
        "aggregations": payroll_aggregations(payroll),
        "scored": scored,
        "metrics": metrics,
        "model_comparison": comparison,
        "category_error_analysis": category,
        "backtest": backtest,
        "review_queue": queue,
    }
    if write_outputs:
        write_pipeline_outputs(results, config)
    return results


def write_pipeline_outputs(results: dict[str, object], config: PayrollConfig = PayrollConfig()) -> None:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    evaluation_dir = config.output_dir / "evaluation"
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    results["payroll"].write_csv(config.data_dir / "synthetic_payroll.csv")
    results["labels"].write_csv(config.data_dir / "synthetic_payroll_labels.csv")
    results["scored"].write_csv(evaluation_dir / "scored_payroll.csv")
    results["metrics"].write_csv(evaluation_dir / "review_budget_metrics.csv")
    results["model_comparison"].write_csv(evaluation_dir / "model_comparison.csv")
    results["category_error_analysis"].write_csv(evaluation_dir / "category_error_analysis.csv")
    results["backtest"].write_csv(evaluation_dir / "backtest_metrics.csv")
    results["review_queue"].write_csv(evaluation_dir / "review_queue.csv")


if __name__ == "__main__":
    run_pipeline(write_outputs=True)
