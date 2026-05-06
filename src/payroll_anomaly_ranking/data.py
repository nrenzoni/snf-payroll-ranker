from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl

from payroll_anomaly_ranking.config import PayrollConfig


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


def generate_employees(config: PayrollConfig = PayrollConfig()) -> pl.DataFrame:
    rng = np.random.default_rng(config.seed)
    employee_ids = [f"SYN-E{idx:05d}" for idx in range(1, config.employee_count + 1)]
    departments = rng.choice(DEPARTMENTS, config.employee_count, p=[0.24, 0.18, 0.20, 0.13, 0.17, 0.08])
    pay_types = rng.choice(["hourly", "salaried"], config.employee_count, p=[0.58, 0.42])
    job_families = [rng.choice(JOB_FAMILIES[dept]) for dept in departments]
    locations = rng.choice(LOCATIONS, config.employee_count)
    job_levels = rng.choice([1, 2, 3, 4, 5], config.employee_count, p=[0.26, 0.31, 0.24, 0.14, 0.05])
    tenure_months = rng.integers(0, 121, config.employee_count)
    start = date(2024, 1, 5)
    hire_dates = [start - timedelta(days=int(months * 30 + rng.integers(0, 30))) for months in tenure_months]
    terminated = rng.random(config.employee_count) < 0.07
    termination_dates = [
        start + timedelta(days=int(rng.integers(120, config.pay_periods * 14 + 30))) if flag else None
        for flag in terminated
    ]
    hourly_rates = np.clip(rng.normal(28 + job_levels * 8, 6), 18, 95)
    salary_period_rates = np.clip(rng.normal(2600 + job_levels * 950, 550), 1800, 9000)
    pay_rates = np.where(pay_types == "hourly", hourly_rates, salary_period_rates)
    return pl.DataFrame(
        {
            "employee_id": employee_ids,
            "manager_id": [f"SYN-M{int(i):04d}" for i in rng.integers(1, 80, config.employee_count)],
            "department": departments,
            "job_family": job_families,
            "location": locations,
            "job_level": job_levels,
            "pay_type": pay_types,
            "hire_date": hire_dates,
            "termination_date": termination_dates,
            "base_pay_rate": np.round(pay_rates, 2),
        }
    )


def generate_pay_periods(config: PayrollConfig = PayrollConfig()) -> pl.DataFrame:
    start = date(2024, 1, 5)
    return pl.DataFrame(
        {
            "pay_period_index": list(range(1, config.pay_periods + 1)),
            "pay_period_start": [start + timedelta(days=(idx - 1) * 14) for idx in range(1, config.pay_periods + 1)],
            "pay_period_end": [start + timedelta(days=(idx - 1) * 14 + 13) for idx in range(1, config.pay_periods + 1)],
        }
    )


def generate_payroll(config: PayrollConfig = PayrollConfig()) -> tuple[pl.DataFrame, pl.DataFrame]:
    rng = np.random.default_rng(config.seed)
    employees = generate_employees(config)
    periods = generate_pay_periods(config)
    rows: list[dict[str, object]] = []
    for emp in employees.iter_rows(named=True):
        promotion_period = int(rng.integers(5, config.pay_periods + 1)) if rng.random() < 0.16 else None
        for period in periods.iter_rows(named=True):
            period_end = period["pay_period_end"]
            active = period_end >= emp["hire_date"] and (emp["termination_date"] is None or period_end <= emp["termination_date"])
            if not active and rng.random() > 0.03:
                continue
            seasonal = 1 + 0.06 * np.sin(period["pay_period_index"] / config.pay_periods * 2 * np.pi)
            promoted = promotion_period is not None and period["pay_period_index"] >= promotion_period
            pay_rate = float(emp["base_pay_rate"]) * (1.09 if promoted else 1.0)
            hourly = emp["pay_type"] == "hourly"
            regular_hours = float(np.clip(rng.normal(78, 5), 45, 86)) if hourly else 80.0
            overtime_base = 2.5 + (emp["department"] in ["Operations", "Support"]) * 3.0
            overtime_hours = float(max(0, rng.gamma(1.5, overtime_base / 1.5) * seasonal)) if hourly else float(max(0, rng.normal(1.0, 1.2)))
            gross = regular_hours * pay_rate + overtime_hours * pay_rate * 1.5 if hourly else pay_rate * seasonal
            bonus = float(rng.gamma(1.3, 550)) if emp["department"] in ["Sales", "Engineering"] and rng.random() < 0.12 else 0.0
            commission = float(rng.gamma(2.0, 420)) if emp["department"] == "Sales" and rng.random() < 0.30 else 0.0
            retro_pay = float(rng.gamma(1.4, 260)) if rng.random() < 0.025 else 0.0
            manual_adjustment = float(rng.normal(0, 160)) if rng.random() < 0.05 else 0.0
            gross_pay = max(0.0, gross + bonus + commission + retro_pay + manual_adjustment + rng.normal(0, 65))
            deduction_rate = float(np.clip(rng.normal(0.23, 0.045), 0.08, 0.38))
            deductions = max(0.0, gross_pay * deduction_rate + rng.normal(0, 25))
            if rng.random() < 0.003:
                deductions = None
            net_pay = gross_pay - (deductions or 0.0)
            rows.append(
                {
                    **emp,
                    **period,
                    "employment_status": "active" if active else "terminated",
                    "tenure_months": max(0, int((period_end - emp["hire_date"]).days / 30)),
                    "regular_hours": round(regular_hours, 2),
                    "overtime_hours": round(overtime_hours, 2),
                    "pay_rate": round(pay_rate, 2),
                    "bonus": round(bonus, 2),
                    "commission": round(commission, 2),
                    "retro_pay": round(retro_pay, 2),
                    "manual_adjustment": round(manual_adjustment, 2),
                    "gross_pay": round(gross_pay, 2),
                    "deductions": None if deductions is None else round(deductions, 2),
                    "net_pay": round(net_pay, 2),
                    "is_anomaly": 0,
                    "anomaly_category": "normal",
                    "anomaly_dollars": 0.0,
                }
            )
    payroll = pl.DataFrame(rows, infer_schema_length=None).with_row_index("record_id")
    return inject_anomalies(payroll, config)


def inject_anomalies(payroll: pl.DataFrame, config: PayrollConfig = PayrollConfig()) -> tuple[pl.DataFrame, pl.DataFrame]:
    rng = np.random.default_rng(config.seed + 11)
    payroll = payroll.clone()
    target_count = min(max(60, payroll.height // 70), payroll.height // 8)
    anomaly_indices = rng.choice(payroll.height, target_count, replace=False)
    categories = rng.choice(ANOMALY_CATEGORIES, target_count)
    rows = payroll.to_dicts()
    labels: list[dict[str, object]] = []
    department_spike_period = int(rng.integers(8, max(9, config.pay_periods - 2)))
    department_spike_department = str(rng.choice(DEPARTMENTS))
    for idx, category in zip(anomaly_indices, categories, strict=False):
        row = rows[int(idx)]
        original = float(row["gross_pay"])
        if category == "duplicate_payment":
            row["gross_pay"] = round(original * 2, 2)
            row["net_pay"] = round(float(row["net_pay"]) * 2, 2)
        elif category == "overtime_spike":
            row["overtime_hours"] = round(max(float(row["overtime_hours"]) * 5, 35), 2)
            row["gross_pay"] = round(original + float(row["overtime_hours"]) * float(row["pay_rate"]) * 1.5, 2)
        elif category == "pay_after_termination":
            row["employment_status"] = "terminated"
            row["termination_date"] = row["pay_period_start"] - timedelta(days=14)
        elif category == "gross_pay_spike":
            row["gross_pay"] = round(original * float(rng.uniform(2.2, 4.0)), 2)
        elif category == "incorrect_pay_rate":
            row["pay_rate"] = round(float(row["pay_rate"]) * float(rng.uniform(1.45, 2.2)), 2)
            row["gross_pay"] = round(original * float(rng.uniform(1.35, 1.9)), 2)
        elif category == "missing_deduction":
            row["deductions"] = 0.0
        elif category == "negative_net_pay":
            row["deductions"] = round(float(row["gross_pay"]) * 1.35, 2)
            row["net_pay"] = round(float(row["gross_pay"]) - float(row["deductions"]), 2)
        elif category == "retro_pay_outlier":
            row["retro_pay"] = round(max(float(row["retro_pay"]), original * 1.2), 2)
            row["gross_pay"] = round(original + float(row["retro_pay"]), 2)
        elif category == "department_payroll_spike":
            row["department"] = department_spike_department
            row["pay_period_index"] = department_spike_period
            row["gross_pay"] = round(original * 1.9, 2)
        elif category == "new_employee_large_payment":
            row["hire_date"] = row["pay_period_start"] - timedelta(days=10)
            row["tenure_months"] = 0
            row["gross_pay"] = round(original * 2.4, 2)
        if category not in ["negative_net_pay", "missing_deduction", "duplicate_payment"]:
            deductions = float(row["deductions"] or 0.0)
            row["net_pay"] = round(float(row["gross_pay"]) - deductions, 2)
        row["is_anomaly"] = 1
        row["anomaly_category"] = category
        row["anomaly_dollars"] = round(abs(float(row["gross_pay"]) - original), 2)
        rows[int(idx)] = row
        labels.append({"record_id": row["record_id"], "anomaly_category": category, "anomaly_dollars": row["anomaly_dollars"]})
    return pl.DataFrame(rows, infer_schema_length=None), pl.DataFrame(labels, infer_schema_length=None)


def write_synthetic_data(config: PayrollConfig = PayrollConfig()) -> tuple[pl.DataFrame, pl.DataFrame]:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    payroll, labels = generate_payroll(config)
    payroll.write_csv(config.data_dir / "synthetic_payroll.csv")
    labels.write_csv(config.data_dir / "synthetic_payroll_labels.csv")
    return payroll, labels
