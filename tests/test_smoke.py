from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.data import generate_payroll
from payroll_anomaly_ranking.evaluation import evaluate_scores
from payroll_anomaly_ranking.explainability import build_review_queue
from payroll_anomaly_ranking.features import build_features
from payroll_anomaly_ranking.models import score_payroll
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
