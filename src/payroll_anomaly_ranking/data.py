from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import polars as pl

from payroll_anomaly_ranking.columns import PayrollCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.scenarios import (
    AnomalyPlan,
    ChangePointEvent,
    DriftPlan,
    ScenarioSpec,
)

DEPARTMENTS = ["Operations", "Sales", "Engineering", "Finance", "Support", "HR"]
JOB_FAMILIES = {
    "Operations": ["Warehouse", "Fulfillment", "Supervisor"],
    "Sales": ["Account Executive", "Sales Ops", "Manager"],
    "Engineering": ["Software", "Data", "Infrastructure"],
    "Finance": ["Payroll", "Accounting", "Analyst"],
    "Support": ["Customer Support", "Technical Support", "Lead"],
    "HR": ["People Ops", "Recruiting", "Benefits"],
}
LOCATIONS = ["Austin", "Chicago", "Denver", "Remote", "Seattle"]
ANOMALY_CATEGORIES = [
    "duplicate_payment",
    "overtime_spike",
    "pay_after_termination",
    "gross_pay_spike",
    "incorrect_pay_rate",
    "missing_deduction",
    "negative_net_pay",
    "retro_pay_outlier",
    "department_payroll_spike",
    "new_employee_large_payment",
]
BASE_PAY_CODES = ["REG", "OT", "SAL", "BON", "COM", "RET"]
LATE_PERIOD_PAY_CODES = ["SHIFT", "SPEC", "ADJX"]


def generate_employees(config: PayrollConfig = PayrollConfig()) -> pl.DataFrame:
    rng = np.random.default_rng(config.seed)
    employee_ids = [f"SYN-E{idx:05d}" for idx in range(1, config.employee_count + 1)]
    departments = rng.choice(
        DEPARTMENTS,
        config.employee_count,
        p=[0.24, 0.18, 0.20, 0.13, 0.17, 0.08],
    )
    pay_types = rng.choice(
        ["hourly", "salaried"],
        config.employee_count,
        p=[0.58, 0.42],
    )
    job_families = [rng.choice(JOB_FAMILIES[dept]) for dept in departments]
    locations = rng.choice(LOCATIONS, config.employee_count)
    job_levels = rng.choice(
        [1, 2, 3, 4, 5],
        config.employee_count,
        p=[0.26, 0.31, 0.24, 0.14, 0.05],
    )
    tenure_months = rng.integers(0, 121, config.employee_count)
    start = date(2024, 1, 5)
    hire_dates = [
        start - timedelta(days=int(months * 30 + rng.integers(0, 30)))
        for months in tenure_months
    ]
    terminated = rng.random(config.employee_count) < 0.07
    termination_dates = [
        start + timedelta(days=int(rng.integers(120, config.pay_periods * 14 + 30)))
        if flag
        else None
        for flag in terminated
    ]
    hourly_rates = np.clip(rng.normal(28 + job_levels * 8, 6), 18, 95)
    salary_period_rates = np.clip(rng.normal(2600 + job_levels * 950, 550), 1800, 9000)
    pay_rates = np.where(pay_types == "hourly", hourly_rates, salary_period_rates)
    return pl.DataFrame(
        {
            PayrollCol.EMPLOYEE_ID: employee_ids,
            PayrollCol.MANAGER_ID: [
                f"SYN-M{int(i):04d}" for i in rng.integers(1, 80, config.employee_count)
            ],
            PayrollCol.DEPARTMENT: departments,
            PayrollCol.JOB_FAMILY: job_families,
            PayrollCol.LOCATION: locations,
            PayrollCol.JOB_LEVEL: job_levels,
            PayrollCol.PAY_TYPE: pay_types,
            PayrollCol.HIRE_DATE: hire_dates,
            PayrollCol.TERMINATION_DATE: termination_dates,
            PayrollCol.BASE_PAY_RATE: np.round(pay_rates, 2),
        },
    )


def generate_pay_periods(config: PayrollConfig = PayrollConfig()) -> pl.DataFrame:
    start = date(2024, 1, 5)
    return pl.DataFrame(
        {
            PayrollCol.PAY_PERIOD_INDEX: list(range(1, config.pay_periods + 1)),
            PayrollCol.PAY_PERIOD_START: [
                start + timedelta(days=(idx - 1) * 14)
                for idx in range(1, config.pay_periods + 1)
            ],
            PayrollCol.PAY_PERIOD_END: [
                start + timedelta(days=(idx - 1) * 14 + 13)
                for idx in range(1, config.pay_periods + 1)
            ],
        },
    )


def generate_payroll(
    config: PayrollConfig = PayrollConfig(),
    scenario: ScenarioSpec | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    payroll = generate_baseline_payroll(config)
    if scenario is not None:
        payroll = apply_scenario(payroll, config, scenario)
    anomaly_plan = scenario.anomaly_plan if scenario is not None else None
    return inject_anomalies(payroll, config, anomaly_plan=anomaly_plan)


def generate_baseline_payroll(
    config: PayrollConfig = PayrollConfig(),
) -> pl.DataFrame:
    rng = np.random.default_rng(config.seed)
    employees = generate_employees(config)
    periods = generate_pay_periods(config)
    rows: list[dict[str, object]] = []
    for emp in employees.iter_rows(named=True):
        promotion_period = (
            int(rng.integers(5, config.pay_periods + 1))
            if rng.random() < 0.16
            else None
        )
        for period in periods.iter_rows(named=True):
            period_end = period[PayrollCol.PAY_PERIOD_END]
            active = period_end >= emp[PayrollCol.HIRE_DATE] and (
                emp[PayrollCol.TERMINATION_DATE] is None
                or period_end <= emp[PayrollCol.TERMINATION_DATE]
            )
            if not active and rng.random() > 0.03:
                continue
            seasonal = 1 + 0.06 * np.sin(
                period[PayrollCol.PAY_PERIOD_INDEX] / config.pay_periods * 2 * np.pi,
            )
            promoted = (
                promotion_period is not None
                and period[PayrollCol.PAY_PERIOD_INDEX] >= promotion_period
            )
            pay_rate = float(emp[PayrollCol.BASE_PAY_RATE]) * (
                1.09 if promoted else 1.0
            )
            hourly = emp[PayrollCol.PAY_TYPE] == "hourly"
            regular_hours = (
                float(np.clip(rng.normal(78, 5), 45, 86)) if hourly else 80.0
            )
            overtime_base = (
                2.5 + (emp[PayrollCol.DEPARTMENT] in ["Operations", "Support"]) * 3.0
            )
            overtime_hours = (
                float(max(0, rng.gamma(1.5, overtime_base / 1.5) * seasonal))
                if hourly
                else float(max(0, rng.normal(1.0, 1.2)))
            )
            gross = (
                regular_hours * pay_rate + overtime_hours * pay_rate * 1.5
                if hourly
                else pay_rate * seasonal
            )
            bonus = (
                float(rng.gamma(1.3, 550))
                if emp[PayrollCol.DEPARTMENT] in ["Sales", "Engineering"]
                and rng.random() < 0.12
                else 0.0
            )
            commission = (
                float(rng.gamma(2.0, 420))
                if emp[PayrollCol.DEPARTMENT] == "Sales" and rng.random() < 0.30
                else 0.0
            )
            retro_pay = float(rng.gamma(1.4, 260)) if rng.random() < 0.025 else 0.0
            manual_adjustment = (
                float(rng.normal(0, 160)) if rng.random() < 0.05 else 0.0
            )
            pay_code, ood_context = _pay_code_for_row(
                rng,
                str(emp[PayrollCol.PAY_TYPE]),
                float(overtime_hours),
                float(bonus + commission + retro_pay),
                int(period[PayrollCol.PAY_PERIOD_INDEX]),
                config,
            )
            gross_pay = max(
                0.0,
                gross
                + bonus
                + commission
                + retro_pay
                + manual_adjustment
                + rng.normal(0, 65),
            )
            deduction_rate = float(np.clip(rng.normal(0.23, 0.045), 0.08, 0.38))
            deductions = max(0.0, gross_pay * deduction_rate + rng.normal(0, 25))
            if rng.random() < 0.003:
                deductions = None
            net_pay = gross_pay - (deductions or 0.0)
            rows.append(
                {
                    **emp,
                    **period,
                    PayrollCol.EMPLOYMENT_STATUS: "active" if active else "terminated",
                    PayrollCol.PAY_CODE: pay_code,
                    PayrollCol.TENURE_MONTHS: max(
                        0,
                        int((period_end - emp[PayrollCol.HIRE_DATE]).days / 30),
                    ),
                    PayrollCol.REGULAR_HOURS: round(regular_hours, 2),
                    PayrollCol.OVERTIME_HOURS: round(overtime_hours, 2),
                    PayrollCol.PAY_RATE: round(pay_rate, 2),
                    PayrollCol.BONUS: round(bonus, 2),
                    PayrollCol.COMMISSION: round(commission, 2),
                    PayrollCol.RETRO_PAY: round(retro_pay, 2),
                    PayrollCol.MANUAL_ADJUSTMENT: round(manual_adjustment, 2),
                    PayrollCol.GROSS_PAY: round(gross_pay, 2),
                    PayrollCol.DEDUCTIONS: None
                    if deductions is None
                    else round(deductions, 2),
                    PayrollCol.NET_PAY: round(net_pay, 2),
                    PayrollCol.IS_ANOMALY: 0,
                    PayrollCol.ANOMALY_CATEGORY: "normal",
                    PayrollCol.ANOMALY_DOLLARS: 0.0,
                    PayrollCol.OOD_PAY_CODE_CONTEXT: ood_context,
                },
            )
    payroll = pl.DataFrame(rows, infer_schema_length=None).with_row_index(
        PayrollCol.RECORD_ID,
    )
    return payroll


def apply_scenario(
    payroll: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
    scenario: ScenarioSpec = ScenarioSpec(),
) -> pl.DataFrame:
    rng = np.random.default_rng(config.seed + scenario.seed_offset + 101)
    rows = payroll.to_dicts()
    for plan in scenario.drift_plans:
        _apply_drift_plan(rows, plan, rng)
    for event in scenario.change_points:
        _apply_change_point(rows, event)
    return pl.DataFrame(rows, infer_schema_length=None)


def inject_anomalies(
    payroll: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
    *,
    anomaly_plan: AnomalyPlan | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    rng = np.random.default_rng(config.seed + 11)
    payroll = payroll.clone()
    default_target = min(max(60, payroll.height // 70), payroll.height // 8)
    target_count = (
        min(anomaly_plan.target_count, payroll.height)
        if anomaly_plan is not None and anomaly_plan.target_count is not None
        else default_target
    )
    anomaly_indices = rng.choice(payroll.height, target_count, replace=False)
    category_values = ANOMALY_CATEGORIES
    probabilities = None
    if anomaly_plan is not None and anomaly_plan.category_weights:
        category_values = [
            cat for cat in ANOMALY_CATEGORIES if cat in anomaly_plan.category_weights
        ]
        weights = np.array(
            [anomaly_plan.category_weights[cat] for cat in category_values],
            dtype=float,
        )
        probabilities = weights / weights.sum() if weights.sum() > 0 else None
    categories = rng.choice(category_values, target_count, p=probabilities)
    rows = payroll.to_dicts()
    labels: list[dict[str, object]] = []
    department_spike_period = int(rng.integers(8, max(9, config.pay_periods - 2)))
    department_spike_department = str(rng.choice(DEPARTMENTS))
    for idx, category in zip(anomaly_indices, categories, strict=False):
        row = rows[int(idx)]
        original = float(row[PayrollCol.GROSS_PAY])
        severity = _severity_multiplier(anomaly_plan, str(category))
        if category == "duplicate_payment":
            row[PayrollCol.GROSS_PAY] = round(original * (1 + severity), 2)
            row[PayrollCol.NET_PAY] = round(
                float(row[PayrollCol.NET_PAY]) * (1 + severity),
                2,
            )
        elif category == "overtime_spike":
            row[PayrollCol.OVERTIME_HOURS] = round(
                max(
                    float(row[PayrollCol.OVERTIME_HOURS]) * 5 * severity,
                    35 * severity,
                ),
                2,
            )
            row[PayrollCol.GROSS_PAY] = round(
                original
                + float(row[PayrollCol.OVERTIME_HOURS])
                * float(row[PayrollCol.PAY_RATE])
                * 1.5,
                2,
            )
        elif category == "pay_after_termination":
            row[PayrollCol.EMPLOYMENT_STATUS] = "terminated"
            row[PayrollCol.TERMINATION_DATE] = row[
                PayrollCol.PAY_PERIOD_START
            ] - timedelta(days=14)
        elif category == "gross_pay_spike":
            row[PayrollCol.GROSS_PAY] = round(
                original * float(rng.uniform(2.2, 4.0)) * severity,
                2,
            )
        elif category == "incorrect_pay_rate":
            row[PayrollCol.PAY_RATE] = round(
                float(row[PayrollCol.PAY_RATE])
                * float(rng.uniform(1.45, 2.2))
                * severity,
                2,
            )
            row[PayrollCol.GROSS_PAY] = round(
                original * float(rng.uniform(1.35, 1.9)) * severity,
                2,
            )
        elif category == "missing_deduction":
            row[PayrollCol.DEDUCTIONS] = 0.0
        elif category == "negative_net_pay":
            row[PayrollCol.DEDUCTIONS] = round(
                float(row[PayrollCol.GROSS_PAY]) * 1.35,
                2,
            )
            row[PayrollCol.NET_PAY] = round(
                float(row[PayrollCol.GROSS_PAY]) - float(row[PayrollCol.DEDUCTIONS]),
                2,
            )
        elif category == "retro_pay_outlier":
            row[PayrollCol.RETRO_PAY] = round(
                max(float(row[PayrollCol.RETRO_PAY]), original * 1.2 * severity),
                2,
            )
            row[PayrollCol.GROSS_PAY] = round(
                original + float(row[PayrollCol.RETRO_PAY]),
                2,
            )
        elif category == "department_payroll_spike":
            row[PayrollCol.DEPARTMENT] = department_spike_department
            row[PayrollCol.PAY_PERIOD_INDEX] = department_spike_period
            row[PayrollCol.GROSS_PAY] = round(original * 1.9 * severity, 2)
        elif category == "new_employee_large_payment":
            row[PayrollCol.HIRE_DATE] = row[PayrollCol.PAY_PERIOD_START] - timedelta(
                days=10,
            )
            row[PayrollCol.TENURE_MONTHS] = 0
            row[PayrollCol.GROSS_PAY] = round(original * 2.4 * severity, 2)
        if category not in [
            "negative_net_pay",
            "missing_deduction",
            "duplicate_payment",
        ]:
            deductions = float(row[PayrollCol.DEDUCTIONS] or 0.0)
            row[PayrollCol.NET_PAY] = round(
                float(row[PayrollCol.GROSS_PAY]) - deductions,
                2,
            )
        row[PayrollCol.IS_ANOMALY] = 1
        row[PayrollCol.ANOMALY_CATEGORY] = category
        row[PayrollCol.ANOMALY_DOLLARS] = round(
            abs(float(row[PayrollCol.GROSS_PAY]) - original),
            2,
        )
        rows[int(idx)] = row
        labels.append(
            {
                PayrollCol.RECORD_ID: row[PayrollCol.RECORD_ID],
                PayrollCol.ANOMALY_CATEGORY: category,
                PayrollCol.ANOMALY_DOLLARS: row[PayrollCol.ANOMALY_DOLLARS],
            },
        )
    return pl.DataFrame(rows, infer_schema_length=None), pl.DataFrame(
        labels,
        infer_schema_length=None,
    )


def _severity_multiplier(plan: AnomalyPlan | None, category: str) -> float:
    if plan is None:
        return 1.0
    return max(float(plan.severity_multipliers.get(category, 1.0)), 0.0)


def _apply_drift_plan(
    rows: list[dict[str, object]],
    plan: DriftPlan,
    rng: np.random.Generator,
) -> None:
    pay_codes = list(plan.pay_code_mix_shift)
    pay_code_probabilities = None
    if pay_codes:
        weights = np.array(
            [plan.pay_code_mix_shift[code] for code in pay_codes],
            dtype=float,
        )
        pay_code_probabilities = weights / weights.sum() if weights.sum() > 0 else None
    for row in rows:
        if not _matches_period_and_subgroup(
            row,
            plan.start_period,
            plan.end_period,
            plan.subgroup_filters,
        ):
            continue
        if pay_codes:
            row[PayrollCol.PAY_CODE] = str(
                rng.choice(pay_codes, p=pay_code_probabilities),
            )
            row[PayrollCol.OOD_PAY_CODE_CONTEXT] = "scenario_pay_code_drift"
        _multiply_numeric(row, PayrollCol.OVERTIME_HOURS, plan.overtime_multiplier)
        _multiply_numeric(row, PayrollCol.DEDUCTIONS, plan.deduction_multiplier)
        _multiply_numeric(row, PayrollCol.GROSS_PAY, plan.gross_pay_multiplier)
        if plan.payroll_total_multiplier is not None:
            noise = (
                float(rng.normal(0, plan.multiplier_noise))
                if plan.multiplier_noise
                else 0.0
            )
            _multiply_numeric(
                row,
                PayrollCol.GROSS_PAY,
                max(plan.payroll_total_multiplier + noise, 0.0),
            )
        _recompute_net_pay(row)


def _apply_change_point(rows: list[dict[str, object]], event: ChangePointEvent) -> None:
    for row in rows:
        if not _matches_period_and_subgroup(
            row,
            event.start_period,
            event.end_period,
            event.subgroup_filters,
        ):
            continue
        if event.pay_code is not None:
            row[PayrollCol.PAY_CODE] = event.pay_code
            row[PayrollCol.OOD_PAY_CODE_CONTEXT] = "scenario_change_point_pay_code"
        if event.field in row and isinstance(row[event.field], int | float):
            row[event.field] = round(
                float(row[event.field]) * event.multiplier + event.additive_shift,
                2,
            )
        _recompute_net_pay(row)


def _matches_period_and_subgroup(
    row: dict[str, object],
    start_period: int | None,
    end_period: int | None,
    subgroup_filters: dict[str, object],
) -> bool:
    period = int(row[PayrollCol.PAY_PERIOD_INDEX])
    if start_period is not None and period < start_period:
        return False
    if end_period is not None and period > end_period:
        return False
    for column, expected in subgroup_filters.items():
        actual = row.get(column)
        if isinstance(expected, (list, tuple, set)):
            if actual not in expected:
                return False
        elif actual != expected:
            return False
    return True


def _multiply_numeric(
    row: dict[str, object],
    column: str,
    multiplier: float | None,
) -> None:
    if multiplier is None or row.get(column) is None:
        return
    row[column] = round(float(row[column]) * multiplier, 2)


def _recompute_net_pay(row: dict[str, object]) -> None:
    if row.get(PayrollCol.DEDUCTIONS) is None:
        return
    row[PayrollCol.NET_PAY] = round(
        float(row[PayrollCol.GROSS_PAY]) - float(row[PayrollCol.DEDUCTIONS]),
        2,
    )


def _pay_code_for_row(
    rng: np.random.Generator,
    pay_type: str,
    overtime_hours: float,
    variable_pay: float,
    pay_period_index: int,
    config: PayrollConfig,
) -> tuple[str, str]:
    late_period_start = max(config.pay_periods - 3, 1)
    if pay_period_index >= late_period_start:
        novelty_rate = 0.055 + 0.015 * (pay_period_index - late_period_start)
        if rng.random() < novelty_rate:
            return str(
                rng.choice(LATE_PERIOD_PAY_CODES),
            ), "late_period_new_or_rare_pay_code"
    if variable_pay > 0 and rng.random() < 0.55:
        return str(rng.choice(["BON", "COM", "RET"])), "standard_pay_code"
    if pay_type == "salaried":
        return "SAL", "standard_pay_code"
    if overtime_hours > 6 and rng.random() < 0.45:
        return "OT", "standard_pay_code"
    if rng.random() < 0.01:
        return "MISC", "rare_pay_code"
    return "REG", "standard_pay_code"


def write_synthetic_data(
    config: PayrollConfig = PayrollConfig(),
) -> tuple[pl.DataFrame, pl.DataFrame]:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    payroll, labels = generate_payroll(config)
    payroll.write_csv(config.data_dir / "synthetic_payroll.csv")
    labels.write_csv(config.data_dir / "synthetic_payroll_labels.csv")
    return payroll, labels
