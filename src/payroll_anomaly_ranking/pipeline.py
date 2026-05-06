from __future__ import annotations

from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import write_synthetic_data
from payroll_anomaly_ranking.evaluation import backtest_by_period, evaluate_scores
from payroll_anomaly_ranking.explainability import build_review_queue
from payroll_anomaly_ranking.features import build_features
from payroll_anomaly_ranking.models import score_payroll
from payroll_anomaly_ranking.rules import add_rule_flags
from payroll_anomaly_ranking.validation import payroll_aggregations, validate_payroll


def run_pipeline(config: PayrollConfig = PayrollConfig()) -> dict[str, object]:
    payroll, labels = write_synthetic_data(config)
    failures, warnings = validate_payroll(payroll)
    features = build_features(payroll)
    ruled = add_rule_flags(features)
    scored = score_payroll(ruled, config)
    metrics, comparison, category = evaluate_scores(scored, config)
    backtest = backtest_by_period(scored, config)
    queue = build_review_queue(scored, top_k=max(config.review_budgets))
    (config.output_dir / "evaluation").mkdir(parents=True, exist_ok=True)
    scored.write_csv(config.output_dir / "evaluation" / "scored_payroll.csv")
    metrics.write_csv(config.output_dir / "evaluation" / "review_budget_metrics.csv")
    comparison.write_csv(config.output_dir / "evaluation" / "model_comparison.csv")
    category.write_csv(config.output_dir / "evaluation" / "category_error_analysis.csv")
    backtest.write_csv(config.output_dir / "evaluation" / "backtest_metrics.csv")
    queue.write_csv(config.output_dir / "evaluation" / "review_queue.csv")
    return {
        "payroll": payroll,
        "labels": labels,
        "validation_failures": failures,
        "validation_warnings": warnings,
        "aggregations": payroll_aggregations(payroll),
        "scored": scored,
        "metrics": metrics,
        "model_comparison": comparison,
        "category_error_analysis": category,
        "review_queue": queue,
    }


if __name__ == "__main__":
    run_pipeline()
