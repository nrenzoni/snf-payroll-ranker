from __future__ import annotations

from enum import StrEnum


class PayrollCol(StrEnum):
    RECORD_ID = "record_id"
    SHIFT_ID = "shift_id"
    PAYROLL_LINE_ID = "payroll_line_id"
    EMPLOYEE_PAY_CYCLE_ID = "employee_pay_cycle_id"
    EMPLOYEE_ID = "employee_id"
    MANAGER_ID = "manager_id"
    PAY_PERIOD_INDEX = "pay_period_index"
    PAY_PERIOD_START = "pay_period_start"
    PAY_PERIOD_END = "pay_period_end"
    FACILITY_ID = "facility_id"
    FACILITY_NAME = "facility_name"
    FACILITY_SIZE_TIER = "facility_size_tier"
    REGION = "region"
    PAYROLL_MATURITY = "payroll_maturity"
    STAFFING_PRESSURE = "staffing_pressure"
    UNIT = "unit"
    ROLE = "role"
    LICENSE_TYPE = "license_type"
    SHIFT_DATE = "shift_date"
    SHIFT_TYPE = "shift_type"
    SHIFT_START_HOUR = "shift_start_hour"
    SHIFT_END_HOUR = "shift_end_hour"
    SCHEDULED_HOURS = "scheduled_hours"
    WORKED_HOURS = "worked_hours"
    PAID_HOURS = "paid_hours"
    CLOCK_IN_VARIANCE_MINUTES = "clock_in_variance_minutes"
    CLOCK_OUT_VARIANCE_MINUTES = "clock_out_variance_minutes"
    MISSED_PUNCH = "missed_punch"
    MANUAL_EDIT = "manual_edit"
    SCHEDULE_EXCEPTION = "schedule_exception"
    PAID_WITHOUT_SCHEDULE = "paid_without_schedule"
    APPROVAL_STATUS = "approval_status"
    LABOR_SOURCE = "labor_source"
    HOME_FACILITY_ID = "home_facility_id"
    WORKED_FACILITY_ID = "worked_facility_id"
    PAY_CODE_CATEGORY = "pay_code_category"
    BASE_RATE = "base_rate"
    RATE_MULTIPLIER = "rate_multiplier"
    PREMIUM_PAY = "premium_pay"
    EXPECTED_SHIFT_GROSS_PAY = "expected_shift_gross_pay"
    IS_WEEKEND = "is_weekend"
    IS_HOLIDAY = "is_holiday"
    REST_GAP_HOURS = "rest_gap_hours"
    SAME_DAY_SHIFT_COUNT = "same_day_shift_count"
    CONSECUTIVE_WORKED_DAYS = "consecutive_worked_days"
    SCENARIO_FAMILY = "scenario_family"
    SCENARIO_STATUS = "scenario_status"
    DEPARTMENT = "department"
    JOB_FAMILY = "job_family"
    LOCATION = "location"
    JOB_LEVEL = "job_level"
    EMPLOYMENT_STATUS = "employment_status"
    PAY_TYPE = "pay_type"
    PAY_CODE = "pay_code"
    REGULAR_HOURS = "regular_hours"
    OVERTIME_HOURS = "overtime_hours"
    PAY_RATE = "pay_rate"
    BASE_PAY_RATE = "base_pay_rate"
    GROSS_PAY = "gross_pay"
    DEDUCTIONS = "deductions"
    NET_PAY = "net_pay"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    TENURE_MONTHS = "tenure_months"
    HIRE_DATE = "hire_date"
    TERMINATION_DATE = "termination_date"
    IS_ANOMALY = "is_anomaly"
    ANOMALY_CATEGORY = "anomaly_category"
    ANOMALY_DOLLARS = "anomaly_dollars"
    OOD_PAY_CODE_CONTEXT = "ood_pay_code_context"
    SHIFT_COUNT = "shift_count"
    ANOMALOUS_SHIFT_COUNT = "anomalous_shift_count"
    TOTAL_SCHEDULED_HOURS = "total_scheduled_hours"
    TOTAL_WORKED_HOURS = "total_worked_hours"
    TOTAL_PAID_HOURS = "total_paid_hours"
    TOTAL_REGULAR_HOURS = "total_regular_hours"
    TOTAL_OVERTIME_HOURS = "total_overtime_hours"
    TOTAL_EXPECTED_GROSS_PAY = "total_expected_gross_pay"
    TOTAL_PREMIUM_PAY = "total_premium_pay"
    TOTAL_GROSS_PAY = "total_gross_pay"
    TOTAL_DEDUCTIONS = "total_deductions"
    TOTAL_NET_PAY = "total_net_pay"


class FeatureCol(StrEnum):
    LAG_GROSS_PAY = "lag_gross_pay"
    GROSS_PAY_ROLLING_MEDIAN = "gross_pay_rolling_median"
    GROSS_PAY_ROLLING_STD = "gross_pay_rolling_std"
    OVERTIME_ROLLING_MEDIAN = "overtime_rolling_median"
    GROSS_PAY_PCT_CHANGE = "gross_pay_pct_change"
    GROSS_PAY_CHANGE_RANK = "gross_pay_change_rank"
    DEDUCTION_RATIO = "deduction_ratio"
    DEDUCTION_RATIO_ROLLING_MEDIAN = "deduction_ratio_rolling_median"
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
    STRICT_PEER_GROUP_SIZE = "strict_peer_group_size"
    EFFECTIVE_PEER_REFERENCE_SIZE = "effective_peer_reference_size"
    PRIOR_EMPLOYEE_PAY_PERIOD_COUNT = "prior_employee_pay_period_count"
    OVERTIME_PER_SCHEDULED_HOUR = "overtime_per_scheduled_hour"
    WORKED_TO_SCHEDULED_RATIO = "worked_to_scheduled_ratio"
    PAID_TO_SCHEDULED_RATIO = "paid_to_scheduled_ratio"
    PREMIUM_PAY_SHARE = "premium_pay_share"
    GROSS_TO_EXPECTED_SHIFT_PAY = "gross_to_expected_shift_pay"
    PAID_MINUS_SCHEDULED_HOURS = "paid_minus_scheduled_hours"
    FACILITY_ROLE_SHIFT_GROSS_MEDIAN = "facility_role_shift_gross_median"
    FACILITY_ROLE_SHIFT_HOURS_MEDIAN = "facility_role_shift_hours_median"
    CROSS_FACILITY_ROLE_SHIFT_GROSS_MEDIAN = "cross_facility_role_shift_gross_median"
    FACILITY_GROSS_ROBUST_Z = "facility_gross_robust_z"
    FACILITY_PREMIUM_SHARE_MEDIAN = "facility_premium_share_median"
    PREMIUM_ELIGIBILITY_MISMATCH = "premium_eligibility_mismatch"
    DUPLICATE_PREMIUM_SIGNATURE = "duplicate_premium_signature"
    TRAILING_7_DAY_HOURS = "trailing_7_day_hours"
    PRIOR_DOUBLE_SHIFT_COUNT = "prior_double_shift_count"
    REST_GAP_RISK = "rest_gap_risk"


class RuleCol(StrEnum):
    PAY_AFTER_TERMINATION = "rule_pay_after_termination"
    DUPLICATE_SIGNATURE = "rule_duplicate_signature"
    NONPOSITIVE_ACTIVE_PAY = "rule_nonpositive_active_pay"
    NEGATIVE_NET_PAY = "rule_negative_net_pay"
    NET_EXCEEDS_GROSS = "rule_net_exceeds_gross"
    EXTREME_OVERTIME = "rule_extreme_overtime"
    LARGE_MANUAL_ADJUSTMENT = "rule_large_manual_adjustment"
    PAY_RATE_CHANGE = "rule_pay_rate_change"
    MISSING_DEDUCTION = "rule_missing_deduction"
    PAID_EXCEEDS_SCHEDULED = "rule_paid_exceeds_scheduled"
    DOUBLE_SHIFT_REST_GAP = "rule_double_shift_rest_gap"
    UNSUPPORTED_SHIFT_DIFFERENTIAL = "rule_unsupported_shift_differential"
    UNSUPPORTED_WEEKEND_PREMIUM = "rule_unsupported_weekend_premium"
    DUPLICATE_PREMIUM = "rule_duplicate_premium"
    PREMIUM_WITHOUT_SUPPORT = "rule_premium_without_support"
    SEVERITY_SCORE = "rule_severity_score"
    REASON_CODES = "rule_reason_codes"


class ScoreCol(StrEnum):
    CLASSIFICATION_SCORE = "classification_score"
    REGRESSION_SCORE = "regression_score"
    EXPECTED_VALUE_SCORE = "expected_value_score"
    RANKING_SCORE = "ranking_score"
    RULE_SCORE = "rule_score"
    STATISTICAL_SCORE = "statistical_score"
    HISTORY_SCORE = "history_score"
    PEER_SCORE = "peer_score"
    ML_SCORE = "ml_score"
    ESTIMATED_EXPOSURE = "estimated_exposure"
    EXPOSURE_SCORE = "exposure_score"
    DOLLAR_SCORE = "dollar_score"
    FINAL_ANOMALY_SCORE = "final_anomaly_score"
    FINAL_APPROVAL_EXCEPTION_SCORE = "final_approval_exception_score"
    SCHEDULE_TIMECLOCK_SCORE = "schedule_timeclock_score"
    PREMIUM_ELIGIBILITY_SCORE = "premium_eligibility_score"
    THRESHOLD_GROSS_PAY_FLAG = "threshold_gross_pay_flag"
    THRESHOLD_TOTAL_HOURS_FLAG = "threshold_total_hours_flag"
    THRESHOLD_OVERTIME_HOURS_FLAG = "threshold_overtime_hours_flag"
    THRESHOLD_PREMIUM_DOLLARS_FLAG = "threshold_premium_dollars_flag"
    THRESHOLD_PAID_VS_SCHEDULED_FLAG = "threshold_paid_vs_scheduled_flag"
    THRESHOLD_FACILITY_VARIANCE_FLAG = "threshold_facility_variance_flag"
    THRESHOLD_MANUAL_PACK_FLAG = "threshold_manual_pack_flag"
    PAY_PERIOD_RANK = "pay_period_rank"
    ENSEMBLE_DISAGREEMENT_UNCERTAINTY = "ensemble_disagreement_uncertainty"
    BOOTSTRAP_SCORE_P10 = "bootstrap_score_p10"
    BOOTSTRAP_SCORE_P90 = "bootstrap_score_p90"
    BOOTSTRAP_SCORE_STD = "bootstrap_score_std"
    BOOTSTRAP_INTERVAL_UNCERTAINTY = "bootstrap_interval_uncertainty"
    CONFORMAL_P_VALUE = "conformal_p_value"
    CONFORMAL_PERCENTILE = "conformal_percentile"
    EXPECTED_GROSS_PAY_P10 = "expected_gross_pay_p10"
    EXPECTED_GROSS_PAY_P50 = "expected_gross_pay_p50"
    EXPECTED_GROSS_PAY_P90 = "expected_gross_pay_p90"
    EXPECTED_GROSS_PAY_INTERVAL_WIDTH = "expected_gross_pay_interval_width"
    GROSS_PAY_EXCESS_VS_P90 = "gross_pay_excess_vs_p90"
    PEER_GROUP_UNCERTAINTY = "peer_group_uncertainty"
    EMPLOYEE_HISTORY_UNCERTAINTY = "employee_history_uncertainty"
    DATA_QUALITY_UNCERTAINTY = "data_quality_uncertainty"
    OOD_UNCERTAINTY = "ood_uncertainty"
    COMPOSITE_UNCERTAINTY_SCORE = "composite_uncertainty_score"


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
    PAY_PERIOD_LABEL = "pay_period_label"
    UNCERTAINTY_BUCKET = "uncertainty_bucket"
    PRIMARY_UNCERTAINTY_REASON = "primary_uncertainty_reason"
    UNCERTAINTY_DRIVERS = "uncertainty_drivers"
    WHY_RISKY = "why_risky"
    WHY_UNCERTAIN = "why_uncertain"
    APPROVAL_RISK_CATEGORY = "approval_risk_category"
    RECOMMENDED_ACTION = "recommended_action"
    SOURCE_TO_CHECK = "source_to_check"
    OVERTIME_CONTEXT = "overtime_context"
    PREMIUM_CONTEXT = "premium_context"
    APPROVAL_READINESS = "approval_readiness"


class OutputName(StrEnum):
    ANALYST_REVIEW_QUEUE = "analyst_review_queue.csv"
    ADMIN_APPROVAL_QUEUE = "admin_approval_queue.csv"
    EVALUATION_LABELED_REVIEW_QUEUE = "evaluation_labeled_review_queue.csv"
    FACILITY_APPROVAL_SUMMARY = "facility_approval_summary.csv"


class MetricCol(StrEnum):
    K = "k"
    PRECISION_AT_K = "precision_at_k"
    RECALL_AT_K = "recall_at_k"
    F1_AT_K = "f1_at_k"
    DOLLARS_CAPTURED_AT_K = "dollars_captured_at_k"
    EXPOSURE_CAPTURED_AT_K = "exposure_captured_at_k"
    EXPOSURE_PER_REVIEW = "exposure_per_review"
    FALSE_POSITIVES_AVOIDED = "false_positives_avoided"
    REVIEW_VOLUME = "review_volume"
    NATIVE_REVIEW_BURDEN = "native_review_burden"
    DOLLAR_CAPTURE_RATE = "dollar_capture_rate"
    MISSED_ESTIMATED_EXPOSURE = "missed_estimated_exposure"
    AVERAGE_ANOMALY_RANK = "average_anomaly_rank"
    MEAN_RECIPROCAL_RANK = "mean_reciprocal_rank"
    PR_AUC = "pr_auc"
    UNCERTAINTY_BUCKET = "uncertainty_bucket"
    ANOMALY_RATE = "anomaly_rate"
    COVERAGE = "coverage"
    REVIEW_PRECISION = "review_precision"
    ABSTAINED_RECORDS = "abstained_records"
    NORMAL_INTERVAL_COVERAGE = "normal_interval_coverage"
    ANOMALY_EXCEEDS_P90_RATE = "anomaly_exceeds_p90_rate"


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
    AVG_UNCERTAINTY = "avg_uncertainty"
    AVG_INTERVAL_WIDTH = "avg_interval_width"
    TOTAL_SHIFTS = "total_shifts"
    TOTAL_GROSS_PAY = "total_gross_pay"
    TOTAL_PAID_HOURS = "total_paid_hours"
    TOTAL_PREMIUM_PAY = "total_premium_pay"
    QUEUE_COUNT = "queue_count"
    HIGH_PRIORITY_COUNT = "high_priority_count"
    ESTIMATED_EXPOSURE = "estimated_exposure"


class SNFRole(StrEnum):
    RN = "RN"
    LPN = "LPN"
    CNA = "CNA"
    MED_AIDE = "Med Aide"
    THERAPY = "Therapy"
    DIETARY = "Dietary"
    HOUSEKEEPING = "Housekeeping"
    MAINTENANCE = "Maintenance"
    ADMIN = "Admin"


class LicenseType(StrEnum):
    RN = "RN"
    LPN = "LPN"
    CNA = "CNA"
    MED_AIDE = "Med Aide"
    THERAPY = "Therapy"
    NONE = "None"


class UnitType(StrEnum):
    LONG_TERM_CARE = "Long Term Care"
    SHORT_STAY_REHAB = "Short Stay Rehab"
    MEMORY_CARE = "Memory Care"
    SKILLED_NURSING = "Skilled Nursing"


class ShiftType(StrEnum):
    DAY = "Day"
    EVENING = "Evening"
    NIGHT = "Night"
    DOUBLE = "Double"


class LaborSource(StrEnum):
    EMPLOYEE = "Employee"
    AGENCY = "Agency"
    FLOAT_POOL = "Float Pool"


class PayCodeCategory(StrEnum):
    REGULAR = "Regular"
    OVERTIME = "Overtime"
    SHIFT_DIFF = "Shift Differential"
    WEEKEND_DIFF = "Weekend Differential"
    HOLIDAY = "Holiday"
    CALLBACK = "Callback"
    ORIENTATION = "Orientation"
    MANUAL_ADJUSTMENT = "Manual Adjustment"


class ApprovalStatus(StrEnum):
    APPROVED = "Approved"
    PENDING = "Pending"
    MISSING = "Missing"
    MANUAL_OVERRIDE = "Manual Override"


class SourceToCheck(StrEnum):
    SCHEDULE = "Schedule"
    TIMECLOCK = "Timeclock"
    PAY_CODE = "Pay code"
    PAY_POLICY = "Pay policy"
    FACILITY_ASSIGNMENT = "Facility assignment"
    EMPLOYEE_LIFECYCLE = "Employee lifecycle"


class RecommendedAction(StrEnum):
    CONFIRM_SCHEDULE = "Confirm schedule"
    VERIFY_TIMECLOCK_EDIT = "Verify timeclock edit"
    CONFIRM_PREMIUM_ELIGIBILITY = "Confirm premium eligibility"
    APPROVE_STAFFING_EXCEPTION = "Approve known staffing exception"
    ESCALATE_TO_PAYROLL = "Escalate to payroll"


class ScenarioFamily(StrEnum):
    BASELINE = "baseline"
    OVERTIME_STAFFING_PRESSURE = "overtime_staffing_pressure"
    PREMIUM_MISMATCH = "premium_mismatch"
    AGENCY_FLOAT_LABOR = "agency_float_labor"
    CENSUS_ACUITY = "census_acuity"
    CREDENTIAL_LICENSE = "credential_license"
    PBJ_CATEGORY = "pbj_category"
    MEAL_BREAK_PREMIUM = "meal_break_premium"
    LIFECYCLE = "lifecycle"
    RETRO_RATE = "retro_rate"
    UNION_POLICY = "union_policy"
    NEW_CLIENT_BOOTSTRAP = "new_client_bootstrap"
    PAYROLL_CLOSE_ADJUSTMENT = "payroll_close_adjustment"


class SNFAnomalyCategory(StrEnum):
    NORMAL = "normal"
    OVERTIME_DOUBLE_SHIFT = "overtime_double_shift"
    REST_GAP_RISK = "rest_gap_risk"
    PAID_VS_SCHEDULED_MISMATCH = "paid_vs_scheduled_mismatch"
    UNSUPPORTED_SHIFT_DIFFERENTIAL = "unsupported_shift_differential"
    UNSUPPORTED_WEEKEND_PREMIUM = "unsupported_weekend_premium"
    DUPLICATE_PREMIUM = "duplicate_premium"
    PREMIUM_WITHOUT_SUPPORT = "premium_without_support"


RULE_FLAG_COLUMNS = [
    RuleCol.PAY_AFTER_TERMINATION,
    RuleCol.DUPLICATE_SIGNATURE,
    RuleCol.NONPOSITIVE_ACTIVE_PAY,
    RuleCol.NEGATIVE_NET_PAY,
    RuleCol.NET_EXCEEDS_GROSS,
    RuleCol.EXTREME_OVERTIME,
    RuleCol.LARGE_MANUAL_ADJUSTMENT,
    RuleCol.PAY_RATE_CHANGE,
    RuleCol.MISSING_DEDUCTION,
    RuleCol.PAID_EXCEEDS_SCHEDULED,
    RuleCol.DOUBLE_SHIFT_REST_GAP,
    RuleCol.UNSUPPORTED_SHIFT_DIFFERENTIAL,
    RuleCol.UNSUPPORTED_WEEKEND_PREMIUM,
    RuleCol.DUPLICATE_PREMIUM,
    RuleCol.PREMIUM_WITHOUT_SUPPORT,
]

PEER_GROUP_COLUMNS = [
    PayrollCol.PAY_PERIOD_INDEX,
    PayrollCol.FACILITY_ID,
    PayrollCol.UNIT,
    PayrollCol.ROLE,
    PayrollCol.SHIFT_TYPE,
    PayrollCol.PAY_CODE_CATEGORY,
    FeatureCol.TENURE_BUCKET,
]

MODEL_FEATURE_COLUMNS = [
    PayrollCol.GROSS_PAY,
    PayrollCol.NET_PAY,
    PayrollCol.REGULAR_HOURS,
    PayrollCol.OVERTIME_HOURS,
    PayrollCol.SCHEDULED_HOURS,
    PayrollCol.WORKED_HOURS,
    PayrollCol.PAID_HOURS,
    PayrollCol.PREMIUM_PAY,
    PayrollCol.EXPECTED_SHIFT_GROSS_PAY,
    PayrollCol.CLOCK_IN_VARIANCE_MINUTES,
    PayrollCol.CLOCK_OUT_VARIANCE_MINUTES,
    PayrollCol.PAY_RATE,
    PayrollCol.MANUAL_ADJUSTMENT,
    FeatureCol.GROSS_PAY_PCT_CHANGE,
    FeatureCol.DEDUCTION_RATIO,
    FeatureCol.DEDUCTION_RATIO_ROLLING_MEDIAN,
    FeatureCol.NET_TO_GROSS_RATIO,
    FeatureCol.PEER_GROSS_DEVIATION_RATIO,
    FeatureCol.PEER_OVERTIME_DEVIATION_RATIO,
    FeatureCol.OVERTIME_PER_SCHEDULED_HOUR,
    FeatureCol.WORKED_TO_SCHEDULED_RATIO,
    FeatureCol.PREMIUM_PAY_SHARE,
    FeatureCol.GROSS_TO_EXPECTED_SHIFT_PAY,
    FeatureCol.PAID_MINUS_SCHEDULED_HOURS,
    FeatureCol.FACILITY_GROSS_ROBUST_Z,
    FeatureCol.PREMIUM_ELIGIBILITY_MISMATCH,
    FeatureCol.REST_GAP_RISK,
    FeatureCol.GROSS_PAY_ROBUST_Z,
    FeatureCol.GROSS_PAY_MAD_SCORE,
    RuleCol.SEVERITY_SCORE,
]

REQUIRED_PAYROLL_COLUMNS = {
    PayrollCol.SHIFT_ID,
    PayrollCol.EMPLOYEE_ID,
    PayrollCol.FACILITY_ID,
    PayrollCol.UNIT,
    PayrollCol.ROLE,
    PayrollCol.LICENSE_TYPE,
    PayrollCol.SHIFT_DATE,
    PayrollCol.SHIFT_TYPE,
    PayrollCol.SCHEDULED_HOURS,
    PayrollCol.WORKED_HOURS,
    PayrollCol.PAID_HOURS,
    PayrollCol.PAY_CODE_CATEGORY,
    PayrollCol.APPROVAL_STATUS,
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

REQUIRED_EMPLOYEE_PAY_CYCLE_COLUMNS = {
    PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
    PayrollCol.EMPLOYEE_ID,
    PayrollCol.FACILITY_ID,
    PayrollCol.FACILITY_NAME,
    PayrollCol.PAY_PERIOD_INDEX,
    PayrollCol.PAY_PERIOD_START,
    PayrollCol.PAY_PERIOD_END,
    PayrollCol.ROLE,
    PayrollCol.LICENSE_TYPE,
    PayrollCol.DEPARTMENT,
    PayrollCol.JOB_FAMILY,
    PayrollCol.JOB_LEVEL,
    PayrollCol.PAY_TYPE,
    PayrollCol.BASE_PAY_RATE,
    PayrollCol.HIRE_DATE,
    PayrollCol.TERMINATION_DATE,
    PayrollCol.TENURE_MONTHS,
    PayrollCol.EMPLOYMENT_STATUS,
    PayrollCol.SHIFT_COUNT,
    PayrollCol.TOTAL_SCHEDULED_HOURS,
    PayrollCol.TOTAL_WORKED_HOURS,
    PayrollCol.TOTAL_PAID_HOURS,
    PayrollCol.TOTAL_REGULAR_HOURS,
    PayrollCol.TOTAL_OVERTIME_HOURS,
    PayrollCol.TOTAL_EXPECTED_GROSS_PAY,
    PayrollCol.TOTAL_PREMIUM_PAY,
    PayrollCol.TOTAL_GROSS_PAY,
    PayrollCol.TOTAL_DEDUCTIONS,
    PayrollCol.TOTAL_NET_PAY,
    PayrollCol.IS_ANOMALY,
    PayrollCol.ANOMALY_CATEGORY,
    PayrollCol.ANOMALY_DOLLARS,
    PayrollCol.SCENARIO_FAMILY,
}
