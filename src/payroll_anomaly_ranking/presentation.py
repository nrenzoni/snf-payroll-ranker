from __future__ import annotations

import polars as pl

from payroll_anomaly_ranking.columns import PayrollCol, ReviewCol, ScoreCol


def synthetic_schema_dictionary() -> pl.DataFrame:
    rows = [
        (
            PayrollCol.RECORD_ID,
            "Synthetic row identifier",
            "identifier",
            "Low; synthetic only",
            "Present and unique enough for row-level tracing",
        ),
        (
            PayrollCol.EMPLOYEE_ID,
            "Synthetic employee identifier",
            "identifier",
            "Low; no real employee identity",
            "Required and non-null",
        ),
        (
            PayrollCol.PAY_PERIOD_INDEX,
            "Sequential payroll cycle",
            "period",
            "Low",
            "Required and non-null",
        ),
        (
            PayrollCol.PAY_PERIOD_START,
            "Synthetic cycle start date",
            "date",
            "Low",
            "Start date before end date",
        ),
        (
            PayrollCol.PAY_PERIOD_END,
            "Synthetic cycle end date",
            "date",
            "Low",
            "End date after hire date unless lifecycle exception",
        ),
        (
            PayrollCol.DEPARTMENT,
            "Synthetic cost center grouping",
            "category",
            "Low; fictional organization",
            "Expected known department values",
        ),
        (
            PayrollCol.JOB_FAMILY,
            "Synthetic role grouping",
            "category",
            "Low",
            "Expected within department",
        ),
        (
            PayrollCol.LOCATION,
            "Synthetic work location",
            "category",
            "Low",
            "Expected known location values",
        ),
        (
            PayrollCol.EMPLOYMENT_STATUS,
            "Active or terminated status for the cycle",
            "category",
            "Medium; synthetic lifecycle signal",
            "Consistent with hire and termination dates",
        ),
        (
            PayrollCol.PAY_TYPE,
            "Hourly or salaried pay basis",
            "category",
            "Low",
            "Expected known pay type values",
        ),
        (
            PayrollCol.PAY_CODE,
            "Synthetic payroll earning or adjustment code",
            "category",
            "Low; synthetic code, not real company configuration",
            "Expected known synthetic codes, with reproducible late-period rarity for OOD diagnostics",
        ),
        (
            PayrollCol.REGULAR_HOURS,
            "Regular hours paid in the cycle",
            "numeric",
            "Medium; synthetic payroll amount driver",
            "Non-negative for normal records",
        ),
        (
            PayrollCol.OVERTIME_HOURS,
            "Overtime hours paid in the cycle",
            "numeric",
            "Medium",
            "Extreme values become review warnings or flags",
        ),
        (
            PayrollCol.PAY_RATE,
            "Hourly rate or period salary amount",
            "numeric",
            "Medium; synthetic compensation",
            "Non-negative and stable unless expected change",
        ),
        (
            PayrollCol.GROSS_PAY,
            "Total gross pay before deductions",
            "numeric",
            "Medium; synthetic compensation",
            "Non-negative for normal records",
        ),
        (
            PayrollCol.DEDUCTIONS,
            "Synthetic deductions amount",
            "numeric",
            "Medium",
            "Missing or zero values may require review",
        ),
        (
            PayrollCol.NET_PAY,
            "Gross pay less deductions",
            "numeric",
            "Medium",
            "Negative or unusually high values may require review",
        ),
        (
            PayrollCol.BONUS,
            "Synthetic bonus amount",
            "numeric",
            "Medium",
            "Non-negative",
        ),
        (
            PayrollCol.COMMISSION,
            "Synthetic commission amount",
            "numeric",
            "Medium",
            "Non-negative",
        ),
        (
            PayrollCol.RETRO_PAY,
            "Synthetic retroactive pay amount",
            "numeric",
            "Medium",
            "Large outliers may require review",
        ),
        (
            PayrollCol.MANUAL_ADJUSTMENT,
            "Manual payroll adjustment",
            "numeric",
            "Medium",
            "Large adjustments may require review",
        ),
        (
            PayrollCol.TENURE_MONTHS,
            "Employee tenure at the pay period",
            "numeric",
            "Low",
            "Consistent with hire date",
        ),
        (
            PayrollCol.HIRE_DATE,
            "Synthetic hire date",
            "date",
            "Medium; lifecycle signal",
            "Not after pay period end",
        ),
        (
            PayrollCol.TERMINATION_DATE,
            "Synthetic termination date where applicable",
            "date",
            "Medium; lifecycle signal",
            "Pay after termination is a review exception",
        ),
        (
            PayrollCol.IS_ANOMALY,
            "Injected synthetic evaluation label",
            "evaluation label",
            "Internal synthetic label",
            "Retained for evaluation, not scoring features",
        ),
        (
            PayrollCol.ANOMALY_CATEGORY,
            "Injected synthetic category",
            "evaluation label",
            "Internal synthetic label",
            "Used for error analysis only",
        ),
        (
            PayrollCol.ANOMALY_DOLLARS,
            "Synthetic dollar impact from injected exception",
            "evaluation label",
            "Internal synthetic label",
            "Used for cost-aware evaluation",
        ),
    ]
    return pl.DataFrame(
        rows,
        schema=[
            "field_name",
            "business_meaning",
            "type_or_category",
            "privacy_sensitivity",
            "validation_expectation",
        ],
        orient="row",
    )


def data_quality_summary(
    payroll: pl.DataFrame,
    validation_warnings: pl.DataFrame,
) -> pl.DataFrame:
    missing_values = sum(payroll.select(pl.all().null_count()).row(0))
    invalid_lifecycle = payroll.filter(
        pl.col(PayrollCol.HIRE_DATE) > pl.col(PayrollCol.PAY_PERIOD_END),
    ).height
    terminated_with_pay = payroll.filter(
        (pl.col(PayrollCol.EMPLOYMENT_STATUS) == "terminated")
        & (pl.col(PayrollCol.GROSS_PAY) > 0),
    ).height
    late_pay_code_ood = (
        payroll.filter(
            pl.col(PayrollCol.OOD_PAY_CODE_CONTEXT).is_in(
                ["late_period_new_or_rare_pay_code", "rare_pay_code"],
            ),
        ).height
        if PayrollCol.OOD_PAY_CODE_CONTEXT in payroll.columns
        else 0
    )
    return pl.DataFrame(
        [
            {"measure": "records", "value": payroll.height},
            {
                "measure": "pay_periods",
                "value": payroll.select(
                    pl.n_unique(PayrollCol.PAY_PERIOD_INDEX),
                ).item(),
            },
            {
                "measure": "employees",
                "value": payroll.select(pl.n_unique(PayrollCol.EMPLOYEE_ID)).item(),
            },
            {"measure": "missing_values", "value": missing_values},
            {"measure": "invalid_lifecycle_rows", "value": invalid_lifecycle},
            {"measure": "terminated_records_with_pay", "value": terminated_with_pay},
            {
                "measure": "pay_codes",
                "value": payroll.select(pl.n_unique(PayrollCol.PAY_CODE)).item(),
            },
            {
                "measure": "late_period_pay_code_ood_contexts",
                "value": late_pay_code_ood,
            },
            {"measure": "exception_warning_types", "value": validation_warnings.height},
        ],
    )


def compact_case_cards(review_queue: pl.DataFrame, limit: int = 5) -> pl.DataFrame:
    columns = [
        ReviewCol.RANK,
        PayrollCol.EMPLOYEE_ID,
        PayrollCol.PAY_PERIOD_INDEX,
        ReviewCol.PAY_PERIOD_LABEL,
        ReviewCol.RISK_CATEGORY,
        ScoreCol.FINAL_ANOMALY_SCORE,
        ReviewCol.UNCERTAINTY_BUCKET,
        ScoreCol.COMPOSITE_UNCERTAINTY_SCORE,
        ReviewCol.PRIMARY_REASON,
        ReviewCol.PRIMARY_UNCERTAINTY_REASON,
        ReviewCol.SECONDARY_REASON,
        ReviewCol.EXPECTED_GROSS_PAY,
        PayrollCol.GROSS_PAY,
        ReviewCol.DIFFERENCE_FROM_EXPECTED,
        ReviewCol.PEER_CONTEXT,
        ReviewCol.DOLLARS_AT_RISK,
        ReviewCol.WHY_RISKY,
        ReviewCol.WHY_UNCERTAIN,
        ReviewCol.EXPLANATION,
    ]
    return (
        review_queue.select(columns)
        .head(limit)
        .rename({PayrollCol.GROSS_PAY: ReviewCol.ACTUAL_GROSS_PAY})
    )
