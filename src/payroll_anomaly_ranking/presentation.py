from __future__ import annotations

import polars as pl

from payroll_anomaly_ranking.columns import PayrollCol, ReviewCol, ScoreCol


def synthetic_schema_dictionary() -> pl.DataFrame:
    rows = [
        (
            PayrollCol.SHIFT_ID,
            "Synthetic shift identifier",
            "identifier",
            "Low; synthetic only",
            "Required and non-null",
        ),
        (
            PayrollCol.PAYROLL_LINE_ID,
            "Synthetic payroll line identifier",
            "identifier",
            "Low",
            "Unique enough for row tracing",
        ),
        (
            PayrollCol.EMPLOYEE_ID,
            "Synthetic employee identifier",
            "identifier",
            "Low; no real identity",
            "Required and non-null",
        ),
        (
            PayrollCol.FACILITY_ID,
            "Synthetic SNF facility",
            "category",
            "Low",
            "Expected known facility",
        ),
        (
            PayrollCol.UNIT,
            "Synthetic SNF unit",
            "category",
            "Low",
            "Expected known unit",
        ),
        (
            PayrollCol.ROLE,
            "SNF role such as RN, LPN, CNA, dietary, or housekeeping",
            "category",
            "Low",
            "Expected role enum",
        ),
        (
            PayrollCol.LICENSE_TYPE,
            "Synthetic credential/license category",
            "category",
            "Medium synthetic lifecycle signal",
            "Expected role-aligned value",
        ),
        (
            PayrollCol.SHIFT_DATE,
            "Synthetic worked shift date",
            "date",
            "Low",
            "Falls within pay period",
        ),
        (
            PayrollCol.SHIFT_TYPE,
            "Day/evening/night/double shift",
            "category",
            "Low",
            "Expected shift enum",
        ),
        (
            PayrollCol.SCHEDULED_HOURS,
            "Hours scheduled before payroll approval",
            "numeric",
            "Medium",
            "Non-negative",
        ),
        (
            PayrollCol.WORKED_HOURS,
            "Timeclock-derived worked hours",
            "numeric",
            "Medium",
            "Non-negative",
        ),
        (
            PayrollCol.PAID_HOURS,
            "Hours paid on payroll line",
            "numeric",
            "Medium",
            "Reconciles to payroll amount",
        ),
        (
            PayrollCol.PAY_CODE,
            "Synthetic SNF pay code",
            "category",
            "Low; synthetic code",
            "Expected illustrative code",
        ),
        (
            PayrollCol.PAY_CODE_CATEGORY,
            "Synthetic pay-code category",
            "category",
            "Low",
            "Used for premium eligibility",
        ),
        (
            PayrollCol.PREMIUM_PAY,
            "Shift/weekend premium dollars",
            "numeric",
            "Medium synthetic compensation",
            "Must match policy context or become review warning",
        ),
        (
            PayrollCol.GROSS_PAY,
            "Gross pay for the shift payroll line",
            "numeric",
            "Medium synthetic compensation",
            "Non-negative for normal rows",
        ),
        (
            PayrollCol.APPROVAL_STATUS,
            "Schedule/timeclock approval context",
            "category",
            "Medium synthetic workflow signal",
            "Expected known status",
        ),
        (
            PayrollCol.IS_ANOMALY,
            "Injected synthetic evaluation label",
            "evaluation label",
            "Internal synthetic label",
            "Excluded from scoring and admin outputs",
        ),
        (
            PayrollCol.ANOMALY_CATEGORY,
            "Injected synthetic anomaly category",
            "evaluation label",
            "Internal synthetic label",
            "Used for evaluation only",
        ),
        (
            PayrollCol.ANOMALY_DOLLARS,
            "Synthetic injected dollar impact",
            "evaluation label",
            "Internal synthetic label",
            "Used for diagnostics only",
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
    unsupported_premium = payroll.filter(
        (pl.col(PayrollCol.PREMIUM_PAY) > 0)
        & (pl.col(PayrollCol.SHIFT_TYPE) == "Day")
        & (pl.col(PayrollCol.IS_WEEKEND) == 0),
    ).height
    return pl.DataFrame(
        [
            {"measure": "shift_payroll_lines", "value": payroll.height},
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
            {
                "measure": "facilities",
                "value": payroll.select(pl.n_unique(PayrollCol.FACILITY_ID)).item(),
            },
            {"measure": "missing_values", "value": missing_values},
            {"measure": "unsupported_premium_contexts", "value": unsupported_premium},
            {
                "measure": "missed_punches",
                "value": payroll.filter(pl.col(PayrollCol.MISSED_PUNCH) == 1).height,
            },
            {
                "measure": "manual_edits",
                "value": payroll.filter(pl.col(PayrollCol.MANUAL_EDIT) == 1).height,
            },
            {"measure": "exception_warning_types", "value": validation_warnings.height},
        ],
    )


def compact_case_cards(queue: pl.DataFrame, limit: int = 3) -> pl.DataFrame:
    fields = [
        ReviewCol.RANK,
        PayrollCol.EMPLOYEE_ID,
        PayrollCol.FACILITY_ID,
        PayrollCol.UNIT,
        PayrollCol.ROLE,
        PayrollCol.SHIFT_DATE,
        PayrollCol.SHIFT_TYPE,
        ReviewCol.APPROVAL_RISK_CATEGORY,
        ReviewCol.RECOMMENDED_ACTION,
        ReviewCol.SOURCE_TO_CHECK,
        ReviewCol.PRIMARY_REASON,
        PayrollCol.GROSS_PAY,
        PayrollCol.SCHEDULED_HOURS,
        PayrollCol.PAID_HOURS,
        PayrollCol.PREMIUM_PAY,
        ReviewCol.DOLLARS_AT_RISK,
        ReviewCol.EXPLANATION,
    ]
    return queue.select([field for field in fields if field in queue.columns]).head(
        limit,
    )


def score_summary(scored: pl.DataFrame) -> pl.DataFrame:
    return scored.select(
        pl.mean(ScoreCol.FINAL_ANOMALY_SCORE).alias("mean_approval_exception_score"),
        pl.max(ScoreCol.FINAL_ANOMALY_SCORE).alias("max_approval_exception_score"),
        pl.mean(ScoreCol.ESTIMATED_EXPOSURE).alias("mean_estimated_exposure"),
    )
