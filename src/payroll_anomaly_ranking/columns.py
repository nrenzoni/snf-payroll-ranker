from __future__ import annotations

from enum import StrEnum


class PayrollCol(StrEnum):
    RECORD_ID = "record_id"
    EMPLOYEE_ID = "employee_id"
    MANAGER_ID = "manager_id"
    PAY_PERIOD_INDEX = "pay_period_index"
    PAY_PERIOD_START = "pay_period_start"
    PAY_PERIOD_END = "pay_period_end"
    DEPARTMENT = "department"
    JOB_FAMILY = "job_family"
    LOCATION = "location"
    JOB_LEVEL = "job_level"
    EMPLOYMENT_STATUS = "employment_status"
    PAY_TYPE = "pay_type"
    REGULAR_HOURS = "regular_hours"
    OVERTIME_HOURS = "overtime_hours"
    PAY_RATE = "pay_rate"
    BASE_PAY_RATE = "base_pay_rate"
    GROSS_PAY = "gross_pay"
    DEDUCTIONS = "deductions"
    NET_PAY = "net_pay"
    BONUS = "bonus"
    COMMISSION = "commission"
    RETRO_PAY = "retro_pay"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    TENURE_MONTHS = "tenure_months"
    HIRE_DATE = "hire_date"
    TERMINATION_DATE = "termination_date"
    IS_ANOMALY = "is_anomaly"
    ANOMALY_CATEGORY = "anomaly_category"
    ANOMALY_DOLLARS = "anomaly_dollars"


class FeatureCol(StrEnum):
    LAG_GROSS_PAY = "lag_gross_pay"
    GROSS_PAY_ROLLING_MEDIAN = "gross_pay_rolling_median"
    GROSS_PAY_ROLLING_STD = "gross_pay_rolling_std"
    OVERTIME_ROLLING_MEDIAN = "overtime_rolling_median"
    GROSS_PAY_PCT_CHANGE = "gross_pay_pct_change"
    GROSS_PAY_CHANGE_RANK = "gross_pay_change_rank"
    DEDUCTION_RATIO = "deduction_ratio"
    NET_TO_GROSS_RATIO = "net_to_gross_ratio"
    TENURE_BUCKET = "tenure_bucket"
    PEER_GROSS_MEDIAN = "peer_gross_median"
    PEER_GROSS_MEAN = "peer_gross_mean"
    PEER_GROSS_STD = "peer_gross_std"
    PEER_OVERTIME_MEDIAN = "peer_overtime_median"
    PEER_GROSS_DEVIATION_RATIO = "peer_gross_deviation_ratio"
    PEER_OVERTIME_DEVIATION_RATIO = "peer_overtime_deviation_ratio"
    GROSS_PAY_ROBUST_Z = "gross_pay_robust_z"
    GROSS_PAY_MAD_SCORE = "gross_pay_mad_score"
    GROSS_PAY_IQR_OUTLIER = "gross_pay_iqr_outlier"
    GROSS_PAY_PERCENTILE = "gross_pay_percentile"
    GROSS_PAY_DEVIATION_RATIO = "gross_pay_deviation_ratio"


class RuleCol(StrEnum):
    PAY_AFTER_TERMINATION = "rule_pay_after_termination"
    DUPLICATE_SIGNATURE = "rule_duplicate_signature"
    NONPOSITIVE_ACTIVE_PAY = "rule_nonpositive_active_pay"
    NEGATIVE_NET_PAY = "rule_negative_net_pay"
    NET_EXCEEDS_GROSS = "rule_net_exceeds_gross"
    EXTREME_OVERTIME = "rule_extreme_overtime"
    LARGE_MANUAL_ADJUSTMENT = "rule_large_manual_adjustment"
    PAY_RATE_CHANGE = "rule_pay_rate_change"
    SEVERITY_SCORE = "rule_severity_score"
    REASON_CODES = "rule_reason_codes"


class ScoreCol(StrEnum):
    RULE_SCORE = "rule_score"
    STATISTICAL_SCORE = "statistical_score"
    HISTORY_SCORE = "history_score"
    PEER_SCORE = "peer_score"
    ML_SCORE = "ml_score"
    DOLLAR_SCORE = "dollar_score"
    FINAL_ANOMALY_SCORE = "final_anomaly_score"
    PAY_PERIOD_RANK = "pay_period_rank"


class ReviewCol(StrEnum):
    PRIMARY_REASON = "primary_reason"
    SECONDARY_REASON = "secondary_reason"
    RISK_CATEGORY = "risk_category"
    DIFFERENCE_FROM_EXPECTED = "difference_from_expected"
    EXPLANATION = "explanation"
    RANK = "rank"
    EXPECTED_GROSS_PAY = "expected_gross_pay"
    PEER_CONTEXT = "peer_context"
    DOLLARS_AT_RISK = "dollars_at_risk"
    ACTUAL_GROSS_PAY = "actual_gross_pay"


class MetricCol(StrEnum):
    K = "k"
    PRECISION_AT_K = "precision_at_k"
    RECALL_AT_K = "recall_at_k"
    F1_AT_K = "f1_at_k"
    DOLLARS_CAPTURED_AT_K = "dollars_captured_at_k"
    DOLLAR_CAPTURE_RATE = "dollar_capture_rate"
    AVERAGE_ANOMALY_RANK = "average_anomaly_rank"
    MEAN_RECIPROCAL_RANK = "mean_reciprocal_rank"
    PR_AUC = "pr_auc"


class AggregateCol(StrEnum):
    RECORDS = "records"
    MIN_GROSS_PAY = "min_gross_pay"
    MAX_GROSS_PAY = "max_gross_pay"
    ACTIVE_EMPLOYEES = "active_employees"
    DEPARTMENT_GROSS_PAY = "department_gross_pay"
    MEAN_OVERTIME_HOURS = "mean_overtime_hours"
    MAX_OVERTIME_HOURS = "max_overtime_hours"
    TOTAL_OVERTIME_HOURS = "total_overtime_hours"
    MANUAL_ADJUSTMENT_TOTAL = "manual_adjustment_total"
    MANUAL_ADJUSTMENT_MEAN = "manual_adjustment_mean"
    PAY_RATE_CHANGE = "pay_rate_change"
    PAY_RATE_CHANGES = "pay_rate_changes"
    GROSS_Q25 = "gross_q25"
    GROSS_MEDIAN = "gross_median"
    GROSS_Q75 = "gross_q75"
    MEAN_NET_PAY = "mean_net_pay"
    REVIEWED = "reviewed"
    TRUE_ANOMALIES = "true_anomalies"
    REVIEWED_RECORDS = "reviewed_records"
    TRUE_POSITIVE_REVIEWS = "true_positive_reviews"
    FALSE_NEGATIVES = "false_negatives"
    FALSE_POSITIVES = "false_positives"
    TOP_10_QUEUE = "top_10_queue"
    TOP_25_QUEUE = "top_25_queue"
    SCORE_THRESHOLD_065_QUEUE = "score_threshold_065_queue"
    EXPECTED_TOP_10_PER_PERIOD = "expected_top_10_per_period"
    EXPECTED_TOP_25_PER_PERIOD = "expected_top_25_per_period"
    EXPECTED_THRESHOLD_065_PER_PERIOD = "expected_threshold_065_per_period"


RULE_FLAG_COLUMNS = [
    RuleCol.PAY_AFTER_TERMINATION,
    RuleCol.DUPLICATE_SIGNATURE,
    RuleCol.NONPOSITIVE_ACTIVE_PAY,
    RuleCol.NEGATIVE_NET_PAY,
    RuleCol.NET_EXCEEDS_GROSS,
    RuleCol.EXTREME_OVERTIME,
    RuleCol.LARGE_MANUAL_ADJUSTMENT,
    RuleCol.PAY_RATE_CHANGE,
]

PEER_GROUP_COLUMNS = [
    PayrollCol.PAY_PERIOD_INDEX,
    PayrollCol.DEPARTMENT,
    PayrollCol.JOB_FAMILY,
    PayrollCol.PAY_TYPE,
    PayrollCol.LOCATION,
    FeatureCol.TENURE_BUCKET,
]

MODEL_FEATURE_COLUMNS = [
    PayrollCol.GROSS_PAY,
    PayrollCol.NET_PAY,
    PayrollCol.REGULAR_HOURS,
    PayrollCol.OVERTIME_HOURS,
    PayrollCol.PAY_RATE,
    PayrollCol.BONUS,
    PayrollCol.COMMISSION,
    PayrollCol.RETRO_PAY,
    PayrollCol.MANUAL_ADJUSTMENT,
    FeatureCol.GROSS_PAY_PCT_CHANGE,
    FeatureCol.DEDUCTION_RATIO,
    FeatureCol.NET_TO_GROSS_RATIO,
    FeatureCol.PEER_GROSS_DEVIATION_RATIO,
    FeatureCol.PEER_OVERTIME_DEVIATION_RATIO,
    FeatureCol.GROSS_PAY_ROBUST_Z,
    FeatureCol.GROSS_PAY_MAD_SCORE,
    RuleCol.SEVERITY_SCORE,
]

REQUIRED_PAYROLL_COLUMNS = {
    PayrollCol.EMPLOYEE_ID,
    PayrollCol.PAY_PERIOD_INDEX,
    PayrollCol.DEPARTMENT,
    PayrollCol.JOB_FAMILY,
    PayrollCol.LOCATION,
    PayrollCol.EMPLOYMENT_STATUS,
    PayrollCol.PAY_TYPE,
    PayrollCol.REGULAR_HOURS,
    PayrollCol.OVERTIME_HOURS,
    PayrollCol.PAY_RATE,
    PayrollCol.GROSS_PAY,
    PayrollCol.DEDUCTIONS,
    PayrollCol.NET_PAY,
    PayrollCol.TENURE_MONTHS,
    PayrollCol.HIRE_DATE,
    PayrollCol.TERMINATION_DATE,
}
