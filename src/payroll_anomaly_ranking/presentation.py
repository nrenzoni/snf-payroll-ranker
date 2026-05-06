from __future__ import annotations

import polars as pl


def synthetic_schema_dictionary() -> pl.DataFrame:
    rows = [
        ("record_id", "Synthetic row identifier", "identifier", "Low; synthetic only", "Present and unique enough for row-level tracing"),
        ("employee_id", "Synthetic employee identifier", "identifier", "Low; no real employee identity", "Required and non-null"),
        ("pay_period_index", "Sequential payroll cycle", "period", "Low", "Required and non-null"),
        ("pay_period_start", "Synthetic cycle start date", "date", "Low", "Start date before end date"),
        ("pay_period_end", "Synthetic cycle end date", "date", "Low", "End date after hire date unless lifecycle exception"),
        ("department", "Synthetic cost center grouping", "category", "Low; fictional organization", "Expected known department values"),
        ("job_family", "Synthetic role grouping", "category", "Low", "Expected within department"),
        ("location", "Synthetic work location", "category", "Low", "Expected known location values"),
        ("employment_status", "Active or terminated status for the cycle", "category", "Medium; synthetic lifecycle signal", "Consistent with hire and termination dates"),
        ("pay_type", "Hourly or salaried pay basis", "category", "Low", "Expected known pay type values"),
        ("regular_hours", "Regular hours paid in the cycle", "numeric", "Medium; synthetic payroll amount driver", "Non-negative for normal records"),
        ("overtime_hours", "Overtime hours paid in the cycle", "numeric", "Medium", "Extreme values become review warnings or flags"),
        ("pay_rate", "Hourly rate or period salary amount", "numeric", "Medium; synthetic compensation", "Non-negative and stable unless expected change"),
        ("gross_pay", "Total gross pay before deductions", "numeric", "Medium; synthetic compensation", "Non-negative for normal records"),
        ("deductions", "Synthetic deductions amount", "numeric", "Medium", "Missing or zero values may require review"),
        ("net_pay", "Gross pay less deductions", "numeric", "Medium", "Negative or unusually high values may require review"),
        ("bonus", "Synthetic bonus amount", "numeric", "Medium", "Non-negative"),
        ("commission", "Synthetic commission amount", "numeric", "Medium", "Non-negative"),
        ("retro_pay", "Synthetic retroactive pay amount", "numeric", "Medium", "Large outliers may require review"),
        ("manual_adjustment", "Manual payroll adjustment", "numeric", "Medium", "Large adjustments may require review"),
        ("tenure_months", "Employee tenure at the pay period", "numeric", "Low", "Consistent with hire date"),
        ("hire_date", "Synthetic hire date", "date", "Medium; lifecycle signal", "Not after pay period end"),
        ("termination_date", "Synthetic termination date where applicable", "date", "Medium; lifecycle signal", "Pay after termination is a review exception"),
        ("is_anomaly", "Injected synthetic evaluation label", "evaluation label", "Internal synthetic label", "Retained for evaluation, not scoring features"),
        ("anomaly_category", "Injected synthetic category", "evaluation label", "Internal synthetic label", "Used for error analysis only"),
        ("anomaly_dollars", "Synthetic dollar impact from injected exception", "evaluation label", "Internal synthetic label", "Used for cost-aware evaluation"),
    ]
    return pl.DataFrame(
        rows,
        schema=["field_name", "business_meaning", "type_or_category", "privacy_sensitivity", "validation_expectation"],
        orient="row",
    )


def data_quality_summary(payroll: pl.DataFrame, validation_warnings: pl.DataFrame) -> pl.DataFrame:
    missing_values = sum(payroll.select(pl.all().null_count()).row(0))
    invalid_lifecycle = payroll.filter(pl.col("hire_date") > pl.col("pay_period_end")).height
    terminated_with_pay = payroll.filter((pl.col("employment_status") == "terminated") & (pl.col("gross_pay") > 0)).height
    return pl.DataFrame(
        [
            {"measure": "records", "value": payroll.height},
            {"measure": "pay_periods", "value": payroll.select(pl.n_unique("pay_period_index")).item()},
            {"measure": "employees", "value": payroll.select(pl.n_unique("employee_id")).item()},
            {"measure": "missing_values", "value": missing_values},
            {"measure": "invalid_lifecycle_rows", "value": invalid_lifecycle},
            {"measure": "terminated_records_with_pay", "value": terminated_with_pay},
            {"measure": "exception_warning_types", "value": validation_warnings.height},
        ]
    )


def compact_case_cards(review_queue: pl.DataFrame, limit: int = 5) -> pl.DataFrame:
    columns = [
        "rank",
        "employee_id",
        "pay_period_index",
        "risk_category",
        "primary_reason",
        "secondary_reason",
        "expected_gross_pay",
        "gross_pay",
        "difference_from_expected",
        "peer_context",
        "dollars_at_risk",
        "explanation",
    ]
    return review_queue.select(columns).head(limit).rename({"gross_pay": "actual_gross_pay"})
