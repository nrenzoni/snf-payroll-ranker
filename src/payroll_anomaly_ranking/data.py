from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, cast

import numpy as np
import polars as pl

from payroll_anomaly_ranking.columns import (
    ApprovalStatus,
    LaborSource,
    LicenseType,
    PayCodeCategory,
    PayrollCol,
    ScenarioFamily,
    ShiftType,
    SNFAnomalyCategory,
    SNFRole,
    UnitType,
)
from payroll_anomaly_ranking.config import (
    PayrollConfig,
    SNFPayPolicyConfig,
    validate_snf_config,
)
from payroll_anomaly_ranking.scenarios import ScenarioSpec


@dataclass(frozen=True)
class FacilityProfile:
    facility_id: str
    facility_name: str
    region: str
    size_tier: str
    payroll_maturity: str
    staffing_pressure: float
    units: tuple[UnitType, ...]


@dataclass(frozen=True)
class GeneratedPayroll:
    payroll: pl.DataFrame
    labels: pl.DataFrame
    facilities: pl.DataFrame = field(default_factory=pl.DataFrame)
    employees: pl.DataFrame = field(default_factory=pl.DataFrame)
    schedules: pl.DataFrame = field(default_factory=pl.DataFrame)
    timeclock: pl.DataFrame = field(default_factory=pl.DataFrame)
    facility_rollups: pl.DataFrame = field(default_factory=pl.DataFrame)
    employee_rollups: pl.DataFrame = field(default_factory=pl.DataFrame)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class GeneratedEmployeePayCycles:
    payroll: pl.DataFrame
    labels: pl.DataFrame
    supporting_payroll: pl.DataFrame = field(default_factory=pl.DataFrame)
    facilities: pl.DataFrame = field(default_factory=pl.DataFrame)
    employees: pl.DataFrame = field(default_factory=pl.DataFrame)
    schedules: pl.DataFrame = field(default_factory=pl.DataFrame)
    timeclock: pl.DataFrame = field(default_factory=pl.DataFrame)
    facility_rollups: pl.DataFrame = field(default_factory=pl.DataFrame)
    metadata: dict[str, object] = field(default_factory=dict)


ROLE_LICENSE = {
    SNFRole.RN: LicenseType.RN,
    SNFRole.LPN: LicenseType.LPN,
    SNFRole.CNA: LicenseType.CNA,
    SNFRole.MED_AIDE: LicenseType.MED_AIDE,
    SNFRole.THERAPY: LicenseType.THERAPY,
    SNFRole.DIETARY: LicenseType.NONE,
    SNFRole.HOUSEKEEPING: LicenseType.NONE,
    SNFRole.MAINTENANCE: LicenseType.NONE,
    SNFRole.ADMIN: LicenseType.NONE,
}

ROLE_RATE = {
    SNFRole.RN: (39.0, 7.0),
    SNFRole.LPN: (31.0, 5.0),
    SNFRole.CNA: (21.0, 3.0),
    SNFRole.MED_AIDE: (24.0, 3.5),
    SNFRole.THERAPY: (42.0, 6.0),
    SNFRole.DIETARY: (18.0, 2.5),
    SNFRole.HOUSEKEEPING: (17.0, 2.0),
    SNFRole.MAINTENANCE: (23.0, 3.5),
    SNFRole.ADMIN: (30.0, 5.0),
}

SHIFT_WINDOWS = {
    ShiftType.DAY: (7, 15, 8.0),
    ShiftType.EVENING: (15, 23, 8.0),
    ShiftType.NIGHT: (23, 7, 8.0),
    ShiftType.DOUBLE: (7, 23, 16.0),
}

FUTURE_SCENARIOS = {
    ScenarioFamily.AGENCY_FLOAT_LABOR: "Agency/float labor duplicate and allocation anomalies",
    ScenarioFamily.CENSUS_ACUITY: "Census and acuity adjusted staffing anomalies",
    ScenarioFamily.CREDENTIAL_LICENSE: "Credential/license and role/pay eligibility mismatches",
    ScenarioFamily.PBJ_CATEGORY: "PBJ staffing category mismatches",
    ScenarioFamily.MEAL_BREAK_PREMIUM: "Missed meal break premium anomalies",
    ScenarioFamily.LIFECYCLE: "New hire, termination, and final pay lifecycle exceptions",
    ScenarioFamily.RETRO_RATE: "Retroactive pay and rate correction anomalies",
    ScenarioFamily.UNION_POLICY: "Union or contract policy variation scenarios",
    ScenarioFamily.NEW_CLIENT_BOOTSTRAP: "New client facility bootstrap normalization scenarios",
    ScenarioFamily.PAYROLL_CLOSE_ADJUSTMENT: "Payroll close/reopen adjustment concentration",
}


def generate_payroll(
    config: PayrollConfig = PayrollConfig(),
    scenario: ScenarioSpec | None = None,
) -> GeneratedPayroll:
    policy = SNFPayPolicyConfig()
    validate_snf_config(config, policy)
    rng = np.random.default_rng(config.seed + (scenario.seed_offset if scenario else 0))
    facilities = generate_facilities(config, rng)
    employees = generate_employees(config, facilities, rng)
    schedules = generate_schedules(config, facilities, employees, rng)
    timeclock = generate_timeclock(schedules, facilities, config, policy, rng)
    payroll = generate_payroll_lines(timeclock, policy, rng)
    payroll, labels = inject_anomalies(payroll, config, scenario, policy, rng)
    facility_rollups = facility_pay_period_rollups(payroll)
    employee_rollups = employee_pay_period_rollups(payroll)
    _validate_rollups(payroll, facility_rollups)
    return GeneratedPayroll(
        payroll=payroll,
        labels=labels,
        facilities=facilities,
        employees=employees,
        schedules=schedules,
        timeclock=timeclock,
        facility_rollups=facility_rollups,
        employee_rollups=employee_rollups,
        metadata=scenario_metadata(scenario),
    )


def generate_facilities(
    config: PayrollConfig,
    rng: np.random.Generator,
) -> pl.DataFrame:
    regions = np.array(["Midwest", "Northeast", "Southeast", "West"])
    size_tiers = np.array(["small", "mid", "large"])
    maturities = np.array(["low", "medium", "high"])
    rows: list[dict[str, object]] = []
    for idx in range(1, config.facility_count + 1):
        size = str(rng.choice(size_tiers, p=[0.25, 0.50, 0.25]))
        maturity = str(rng.choice(maturities, p=[0.20, 0.55, 0.25]))
        pressure_base = {"small": 0.95, "mid": 1.0, "large": 1.08}[size]
        pressure = float(np.clip(rng.normal(pressure_base, 0.12), 0.70, 1.40))
        rows.append(
            {
                PayrollCol.FACILITY_ID: f"SNF-F{idx:03d}",
                PayrollCol.FACILITY_NAME: f"Synthetic SNF Facility {idx:02d}",
                PayrollCol.REGION: str(rng.choice(regions)),
                PayrollCol.FACILITY_SIZE_TIER: size,
                PayrollCol.PAYROLL_MATURITY: maturity,
                PayrollCol.STAFFING_PRESSURE: round(pressure, 3),
            },
        )
    return pl.DataFrame(rows)


def generate_employees(
    config: PayrollConfig = PayrollConfig(),
    facilities: pl.DataFrame | None = None,
    rng: np.random.Generator | None = None,
) -> pl.DataFrame:
    validate_snf_config(config)
    rng = rng or np.random.default_rng(config.seed)
    if facilities is None:
        facilities = generate_facilities(config, rng)
    facility_ids = facilities.get_column(PayrollCol.FACILITY_ID).to_numpy()
    roles = np.array(list(SNFRole))
    role_probabilities = np.array(
        [0.10, 0.16, 0.44, 0.06, 0.04, 0.08, 0.06, 0.03, 0.03],
    )
    rows: list[dict[str, object]] = []
    start = date(2024, 1, 1)
    for idx in range(1, config.employee_count + 1):
        role = SNFRole(rng.choice(roles, p=role_probabilities))
        mean_rate, sd_rate = ROLE_RATE[role]
        tenure_months = int(rng.integers(0, 121))
        hire_date = start - timedelta(
            days=int(tenure_months * 30 + rng.integers(0, 30)),
        )
        terminated = rng.random() < 0.04
        termination_date = (
            start + timedelta(days=int(rng.integers(90, config.pay_periods * 14 + 30)))
            if terminated
            else None
        )
        base_rate = float(np.clip(rng.normal(mean_rate, sd_rate), 14.0, 65.0))
        facility_id = str(rng.choice(facility_ids))
        rows.append(
            {
                PayrollCol.EMPLOYEE_ID: f"SYN-SNF-E{idx:05d}",
                PayrollCol.MANAGER_ID: f"SYN-SNF-M{int(rng.integers(1, 80)):04d}",
                PayrollCol.HOME_FACILITY_ID: facility_id,
                PayrollCol.FACILITY_ID: facility_id,
                PayrollCol.WORKED_FACILITY_ID: facility_id,
                PayrollCol.ROLE: role,
                PayrollCol.LICENSE_TYPE: ROLE_LICENSE[role],
                PayrollCol.DEPARTMENT: "Nursing"
                if role in {SNFRole.RN, SNFRole.LPN, SNFRole.CNA, SNFRole.MED_AIDE}
                else "Facility Support",
                PayrollCol.JOB_FAMILY: role,
                PayrollCol.LOCATION: facility_id,
                PayrollCol.JOB_LEVEL: _role_level(role),
                PayrollCol.PAY_TYPE: "hourly",
                PayrollCol.HIRE_DATE: hire_date,
                PayrollCol.TERMINATION_DATE: termination_date,
                PayrollCol.BASE_PAY_RATE: round(base_rate, 2),
            },
        )
    return pl.DataFrame(rows)


def generate_schedules(
    config: PayrollConfig,
    facilities: pl.DataFrame,
    employees: pl.DataFrame,
    rng: np.random.Generator,
) -> pl.DataFrame:
    facility_lookup = facilities.select(
        PayrollCol.FACILITY_ID,
        PayrollCol.FACILITY_NAME,
        PayrollCol.REGION,
        PayrollCol.FACILITY_SIZE_TIER,
        PayrollCol.PAYROLL_MATURITY,
        PayrollCol.STAFFING_PRESSURE,
    )
    employee_rows = employees.join(
        facility_lookup,
        on=PayrollCol.FACILITY_ID,
    ).to_dicts()
    period_start = date(2024, 1, 5)
    rows: list[dict[str, object]] = []
    shift_number = 1
    units = list(UnitType)
    shifts = np.array([ShiftType.DAY, ShiftType.EVENING, ShiftType.NIGHT])
    for emp in employee_rows:
        role = SNFRole(emp[PayrollCol.ROLE])
        role_shift_prob = _role_shift_probabilities(role)
        for period in range(1, config.pay_periods + 1):
            pay_period_start = period_start + timedelta(days=(period - 1) * 14)
            pay_period_end = pay_period_start + timedelta(days=13)
            if pay_period_end < emp[PayrollCol.HIRE_DATE]:
                continue
            if (
                emp[PayrollCol.TERMINATION_DATE] is not None
                and pay_period_start > emp[PayrollCol.TERMINATION_DATE]
            ):
                continue
            pressure = float(emp[PayrollCol.STAFFING_PRESSURE])
            base_count = rng.poisson(config.shifts_per_employee_per_period * pressure)
            shift_count = max(2, min(base_count, 14))
            days = rng.choice(np.arange(14), size=shift_count, replace=shift_count > 14)
            for day in sorted(int(value) for value in days):
                shift_type = ShiftType(rng.choice(shifts, p=role_shift_prob))
                start_hour, end_hour, scheduled_hours = SHIFT_WINDOWS[shift_type]
                shift_date = pay_period_start + timedelta(days=day)
                rows.append(
                    {
                        PayrollCol.SHIFT_ID: f"SYN-SHIFT-{shift_number:08d}",
                        PayrollCol.EMPLOYEE_ID: emp[PayrollCol.EMPLOYEE_ID],
                        PayrollCol.MANAGER_ID: emp[PayrollCol.MANAGER_ID],
                        PayrollCol.FACILITY_ID: emp[PayrollCol.FACILITY_ID],
                        PayrollCol.FACILITY_NAME: emp[PayrollCol.FACILITY_NAME],
                        PayrollCol.REGION: emp[PayrollCol.REGION],
                        PayrollCol.FACILITY_SIZE_TIER: emp[
                            PayrollCol.FACILITY_SIZE_TIER
                        ],
                        PayrollCol.PAYROLL_MATURITY: emp[PayrollCol.PAYROLL_MATURITY],
                        PayrollCol.STAFFING_PRESSURE: emp[PayrollCol.STAFFING_PRESSURE],
                        PayrollCol.HOME_FACILITY_ID: emp[PayrollCol.HOME_FACILITY_ID],
                        PayrollCol.WORKED_FACILITY_ID: emp[
                            PayrollCol.WORKED_FACILITY_ID
                        ],
                        PayrollCol.UNIT: str(rng.choice(units)),
                        PayrollCol.ROLE: emp[PayrollCol.ROLE],
                        PayrollCol.LICENSE_TYPE: emp[PayrollCol.LICENSE_TYPE],
                        PayrollCol.DEPARTMENT: emp[PayrollCol.DEPARTMENT],
                        PayrollCol.JOB_FAMILY: emp[PayrollCol.JOB_FAMILY],
                        PayrollCol.LOCATION: emp[PayrollCol.LOCATION],
                        PayrollCol.JOB_LEVEL: emp[PayrollCol.JOB_LEVEL],
                        PayrollCol.PAY_TYPE: emp[PayrollCol.PAY_TYPE],
                        PayrollCol.LABOR_SOURCE: LaborSource.EMPLOYEE,
                        PayrollCol.PAY_PERIOD_INDEX: period,
                        PayrollCol.PAY_PERIOD_START: pay_period_start,
                        PayrollCol.PAY_PERIOD_END: pay_period_end,
                        PayrollCol.SHIFT_DATE: shift_date,
                        PayrollCol.SHIFT_TYPE: shift_type,
                        PayrollCol.SHIFT_START_HOUR: start_hour,
                        PayrollCol.SHIFT_END_HOUR: end_hour,
                        PayrollCol.SCHEDULED_HOURS: scheduled_hours,
                        PayrollCol.BASE_PAY_RATE: emp[PayrollCol.BASE_PAY_RATE],
                        PayrollCol.HIRE_DATE: emp[PayrollCol.HIRE_DATE],
                        PayrollCol.TERMINATION_DATE: emp[PayrollCol.TERMINATION_DATE],
                    },
                )
                shift_number += 1
    return pl.DataFrame(rows, infer_schema_length=None)


def generate_timeclock(
    schedules: pl.DataFrame,
    facilities: pl.DataFrame,
    config: PayrollConfig,
    policy: SNFPayPolicyConfig,
    rng: np.random.Generator,
) -> pl.DataFrame:
    rows = schedules.to_dicts()
    for row in rows:
        maturity = str(row[PayrollCol.PAYROLL_MATURITY])
        pressure = float(row[PayrollCol.STAFFING_PRESSURE])
        missed_rate = {"low": 0.060, "medium": 0.035, "high": 0.018}[maturity]
        manual_rate = {"low": 0.090, "medium": 0.055, "high": 0.025}[maturity]
        scheduled = float(row[PayrollCol.SCHEDULED_HOURS])
        clock_in_variance = rng.normal(0, 9 + pressure * 2)
        clock_out_variance = rng.normal(0, 10 + pressure * 3)
        worked_hours = max(
            0.0,
            scheduled + (clock_out_variance - clock_in_variance) / 60,
        )
        if rng.random() < 0.045 * pressure:
            worked_hours += rng.uniform(1.0, 4.0)
        if rng.random() < 0.018 * pressure:
            row[PayrollCol.SHIFT_TYPE] = ShiftType.DOUBLE
            row[PayrollCol.SHIFT_END_HOUR] = 23
            row[PayrollCol.SCHEDULED_HOURS] = 16.0
            worked_hours = max(worked_hours, rng.normal(15.5, 0.5))
        missed_punch = rng.random() < missed_rate
        manual_edit = missed_punch or rng.random() < manual_rate
        row[PayrollCol.WORKED_HOURS] = round(worked_hours, 2)
        row[PayrollCol.PAID_HOURS] = round(
            max(worked_hours, scheduled if manual_edit else worked_hours),
            2,
        )
        row[PayrollCol.REGULAR_HOURS] = round(
            min(row[PayrollCol.PAID_HOURS], policy.overtime_daily_hours),
            2,
        )
        row[PayrollCol.OVERTIME_HOURS] = round(
            max(row[PayrollCol.PAID_HOURS] - policy.overtime_daily_hours, 0.0),
            2,
        )
        row[PayrollCol.CLOCK_IN_VARIANCE_MINUTES] = round(clock_in_variance, 1)
        row[PayrollCol.CLOCK_OUT_VARIANCE_MINUTES] = round(clock_out_variance, 1)
        row[PayrollCol.MISSED_PUNCH] = int(missed_punch)
        row[PayrollCol.MANUAL_EDIT] = int(manual_edit)
        row[PayrollCol.SCHEDULE_EXCEPTION] = int(
            abs(row[PayrollCol.PAID_HOURS] - scheduled) > 1.0,
        )
        row[PayrollCol.PAID_WITHOUT_SCHEDULE] = 0
        row[PayrollCol.APPROVAL_STATUS] = (
            ApprovalStatus.MANUAL_OVERRIDE if manual_edit else ApprovalStatus.APPROVED
        )
    timed = pl.DataFrame(rows, infer_schema_length=None)
    return _add_fatigue_context(timed, policy)


def generate_payroll_lines(
    timeclock: pl.DataFrame,
    policy: SNFPayPolicyConfig,
    rng: np.random.Generator,
) -> pl.DataFrame:
    rows = timeclock.to_dicts()
    output: list[dict[str, object]] = []
    for index, row in enumerate(rows, start=1):
        base_rate = float(row[PayrollCol.BASE_PAY_RATE])
        regular_hours = float(row[PayrollCol.REGULAR_HOURS])
        overtime_hours = float(row[PayrollCol.OVERTIME_HOURS])
        shift_type = ShiftType(row[PayrollCol.SHIFT_TYPE])
        is_weekend = _is_weekend(row[PayrollCol.SHIFT_DATE])
        shift_diff_rate = _shift_diff_rate(shift_type, policy)
        weekend_rate = policy.weekend_diff_rate if is_weekend else 0.0
        regular_pay = regular_hours * base_rate
        overtime_pay = overtime_hours * base_rate * policy.overtime_multiplier
        premium_pay = float(row[PayrollCol.PAID_HOURS]) * (
            shift_diff_rate + weekend_rate
        )
        gross = regular_pay + overtime_pay + premium_pay
        deductions = gross * float(np.clip(rng.normal(0.21, 0.025), 0.12, 0.33))
        category = _primary_pay_code_category(
            overtime_hours,
            premium_pay,
            shift_type,
            is_weekend,
        )
        pay_code = _pay_code(category, shift_type, is_weekend)
        ood_context = "standard_snf_pay_code"
        if int(row[PayrollCol.PAY_PERIOD_INDEX]) >= max(
            1,
            0,
        ) and rng.random() < _late_pay_code_rate(row):
            pay_code = str(rng.choice(["SNF_CRIT", "SNF_PREM", "SNF_RARE"]))
            ood_context = "late_period_new_or_rare_pay_code"
        output.append(
            {
                **row,
                PayrollCol.RECORD_ID: index - 1,
                PayrollCol.PAYROLL_LINE_ID: f"SYN-PL-{index:08d}",
                PayrollCol.PAY_CODE: pay_code,
                PayrollCol.PAY_CODE_CATEGORY: category,
                PayrollCol.PAY_RATE: round(base_rate, 2),
                PayrollCol.BASE_RATE: round(base_rate, 2),
                PayrollCol.RATE_MULTIPLIER: policy.overtime_multiplier
                if overtime_hours
                else 1.0,
                PayrollCol.PREMIUM_PAY: round(premium_pay, 2),
                PayrollCol.EXPECTED_SHIFT_GROSS_PAY: round(
                    float(row[PayrollCol.SCHEDULED_HOURS]) * base_rate + premium_pay,
                    2,
                ),
                PayrollCol.GROSS_PAY: round(gross, 2),
                PayrollCol.DEDUCTIONS: round(deductions, 2),
                PayrollCol.NET_PAY: round(gross - deductions, 2),
                PayrollCol.MANUAL_ADJUSTMENT: 0.0,
                PayrollCol.TENURE_MONTHS: max(
                    0,
                    int(
                        (row[PayrollCol.SHIFT_DATE] - row[PayrollCol.HIRE_DATE]).days
                        / 30,
                    ),
                ),
                PayrollCol.EMPLOYMENT_STATUS: _employment_status(row),
                PayrollCol.IS_WEEKEND: int(is_weekend),
                PayrollCol.IS_HOLIDAY: 0,
                PayrollCol.IS_ANOMALY: 0,
                PayrollCol.ANOMALY_CATEGORY: SNFAnomalyCategory.NORMAL,
                PayrollCol.ANOMALY_DOLLARS: 0.0,
                PayrollCol.OOD_PAY_CODE_CONTEXT: ood_context,
            },
        )
    return pl.DataFrame(output, infer_schema_length=None)


def inject_anomalies(
    payroll: pl.DataFrame,
    config: PayrollConfig,
    scenario: ScenarioSpec | None,
    policy: SNFPayPolicyConfig,
    rng: np.random.Generator,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    rows = payroll.to_dicts()
    if not rows:
        return payroll, pl.DataFrame()
    family = _scenario_family(scenario)
    target_count = _scenario_target_count(scenario, rows)
    candidates = _scenario_candidates(rows, family)
    if not candidates:
        candidates = list(range(len(rows)))
    selected = rng.choice(candidates, min(target_count, len(candidates)), replace=False)
    labels: list[dict[str, object]] = []
    for raw_idx in selected:
        idx = int(raw_idx)
        row = rows[idx]
        original = float(row[PayrollCol.GROSS_PAY])
        if family == ScenarioFamily.PREMIUM_MISMATCH:
            category = _inject_premium_mismatch(row, policy, rng)
        else:
            category = _inject_overtime_pressure(row, policy, rng)
            if scenario is not None and scenario.anomaly_plan is not None:
                if "overtime_spike" in scenario.anomaly_plan.category_weights:
                    category = "overtime_spike"
        row[PayrollCol.IS_ANOMALY] = 1
        row[PayrollCol.ANOMALY_CATEGORY] = category
        row[PayrollCol.SCENARIO_FAMILY] = family
        row[PayrollCol.SCENARIO_STATUS] = "implemented"
        row[PayrollCol.ANOMALY_DOLLARS] = round(
            abs(float(row[PayrollCol.GROSS_PAY]) - original),
            2,
        )
        labels.append(
            {
                PayrollCol.RECORD_ID: row[PayrollCol.RECORD_ID],
                PayrollCol.SHIFT_ID: row[PayrollCol.SHIFT_ID],
                PayrollCol.ANOMALY_CATEGORY: row[PayrollCol.ANOMALY_CATEGORY],
                PayrollCol.ANOMALY_DOLLARS: row[PayrollCol.ANOMALY_DOLLARS],
                PayrollCol.SCENARIO_FAMILY: family,
            },
        )
        rows[idx] = row
    updated = pl.DataFrame(rows, infer_schema_length=None).with_columns(
        pl.col(PayrollCol.SCENARIO_FAMILY).fill_null(ScenarioFamily.BASELINE),
        pl.col(PayrollCol.SCENARIO_STATUS).fill_null("baseline"),
    )
    updated = _simulate_observed_corrections(updated, rng)
    return updated, pl.DataFrame(labels, infer_schema_length=None)


def facility_pay_period_rollups(payroll: pl.DataFrame) -> pl.DataFrame:
    return payroll.group_by([PayrollCol.PAY_PERIOD_INDEX, PayrollCol.FACILITY_ID]).agg(
        pl.len().alias("total_shifts"),
        pl.sum(PayrollCol.GROSS_PAY).alias("total_gross_pay"),
        pl.sum(PayrollCol.PAID_HOURS).alias("total_paid_hours"),
        pl.sum(PayrollCol.OVERTIME_HOURS).alias("total_overtime_hours"),
        pl.sum(PayrollCol.PREMIUM_PAY).alias("total_premium_pay"),
        pl.sum(PayrollCol.IS_ANOMALY).alias("synthetic_anomaly_count"),
        pl.sum(PayrollCol.ANOMALY_DOLLARS).alias("synthetic_anomaly_dollars"),
    )


def employee_pay_period_rollups(payroll: pl.DataFrame) -> pl.DataFrame:
    return payroll.group_by([PayrollCol.PAY_PERIOD_INDEX, PayrollCol.EMPLOYEE_ID]).agg(
        pl.len().alias("total_shifts"),
        pl.sum(PayrollCol.GROSS_PAY).alias("total_gross_pay"),
        pl.sum(PayrollCol.PAID_HOURS).alias("total_paid_hours"),
        pl.sum(PayrollCol.OVERTIME_HOURS).alias("total_overtime_hours"),
        pl.sum(PayrollCol.PREMIUM_PAY).alias("total_premium_pay"),
    )


def write_synthetic_data(config: PayrollConfig = PayrollConfig()) -> GeneratedPayroll:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    generated = generate_payroll(config)
    generated.payroll.write_csv(config.data_dir / "synthetic_snf_shift_payroll.csv")
    generated.payroll.write_csv(config.data_dir / "synthetic_payroll.csv")
    generated.labels.write_csv(config.data_dir / "synthetic_payroll_labels.csv")
    generated.facility_rollups.write_csv(
        config.data_dir / "synthetic_snf_facility_rollups.csv",
    )
    return generated


def generate_employee_pay_cycles(
    config: PayrollConfig = PayrollConfig(),
    scenario: ScenarioSpec | None = None,
) -> GeneratedEmployeePayCycles:
    generated = generate_payroll(config, scenario=scenario)
    employee_cycles = employee_pay_cycle_records(generated.payroll)
    labels = employee_pay_cycle_labels(employee_cycles)
    return GeneratedEmployeePayCycles(
        payroll=employee_cycles,
        labels=labels,
        supporting_payroll=generated.payroll,
        facilities=generated.facilities,
        employees=generated.employees,
        schedules=generated.schedules,
        timeclock=generated.timeclock,
        facility_rollups=generated.facility_rollups,
        metadata=generated.metadata,
    )


def scenario_metadata(scenario: ScenarioSpec | None) -> dict[str, object]:
    family = _scenario_family(scenario)
    return {
        "name": scenario.name if scenario is not None else "default",
        "scenario_family": family,
        "implemented_scenarios": [
            ScenarioFamily.OVERTIME_STAFFING_PRESSURE,
            ScenarioFamily.PREMIUM_MISMATCH,
        ],
        "future_scenarios": {
            key.value: value for key, value in FUTURE_SCENARIOS.items()
        },
        "policy_assumptions": "Synthetic configurable policy; not legal or payroll advice.",
    }


def employee_pay_cycle_records(payroll: pl.DataFrame) -> pl.DataFrame:
    category_rank = (
        payroll.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
        .group_by(
            [
                PayrollCol.EMPLOYEE_ID,
                PayrollCol.FACILITY_ID,
                PayrollCol.PAY_PERIOD_INDEX,
                PayrollCol.ANOMALY_CATEGORY,
            ],
        )
        .agg(
            pl.sum(PayrollCol.ANOMALY_DOLLARS).alias("category_anomaly_dollars"),
        )
        .sort(
            [
                PayrollCol.EMPLOYEE_ID,
                PayrollCol.FACILITY_ID,
                PayrollCol.PAY_PERIOD_INDEX,
                "category_anomaly_dollars",
                PayrollCol.ANOMALY_CATEGORY,
            ],
            descending=[False, False, False, True, False],
        )
    )
    dominant_category = category_rank.group_by(
        [PayrollCol.EMPLOYEE_ID, PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX],
    ).agg(
        pl.first(PayrollCol.ANOMALY_CATEGORY).alias("dominant_anomaly_category"),
    )
    cycles = payroll.group_by(
        [PayrollCol.EMPLOYEE_ID, PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX],
    ).agg(
        pl.first(PayrollCol.MANAGER_ID).alias(PayrollCol.MANAGER_ID),
        pl.first(PayrollCol.FACILITY_NAME).alias(PayrollCol.FACILITY_NAME),
        pl.first(PayrollCol.REGION).alias(PayrollCol.REGION),
        pl.first(PayrollCol.FACILITY_SIZE_TIER).alias(PayrollCol.FACILITY_SIZE_TIER),
        pl.first(PayrollCol.PAYROLL_MATURITY).alias(PayrollCol.PAYROLL_MATURITY),
        pl.first(PayrollCol.STAFFING_PRESSURE).alias(PayrollCol.STAFFING_PRESSURE),
        pl.first(PayrollCol.HOME_FACILITY_ID).alias(PayrollCol.HOME_FACILITY_ID),
        pl.first(PayrollCol.WORKED_FACILITY_ID).alias(PayrollCol.WORKED_FACILITY_ID),
        pl.first(PayrollCol.ROLE).alias(PayrollCol.ROLE),
        pl.first(PayrollCol.LICENSE_TYPE).alias(PayrollCol.LICENSE_TYPE),
        pl.first(PayrollCol.DEPARTMENT).alias(PayrollCol.DEPARTMENT),
        pl.first(PayrollCol.JOB_FAMILY).alias(PayrollCol.JOB_FAMILY),
        pl.first(PayrollCol.LOCATION).alias(PayrollCol.LOCATION),
        pl.first(PayrollCol.JOB_LEVEL).alias(PayrollCol.JOB_LEVEL),
        pl.first(PayrollCol.PAY_TYPE).alias(PayrollCol.PAY_TYPE),
        pl.first(PayrollCol.PAY_PERIOD_START).alias(PayrollCol.PAY_PERIOD_START),
        pl.first(PayrollCol.PAY_PERIOD_END).alias(PayrollCol.PAY_PERIOD_END),
        pl.first(PayrollCol.BASE_PAY_RATE).alias(PayrollCol.BASE_PAY_RATE),
        pl.max(PayrollCol.TENURE_MONTHS).alias(PayrollCol.TENURE_MONTHS),
        pl.first(PayrollCol.HIRE_DATE).alias(PayrollCol.HIRE_DATE),
        pl.first(PayrollCol.TERMINATION_DATE).alias(PayrollCol.TERMINATION_DATE),
        pl.first(PayrollCol.EMPLOYMENT_STATUS).alias(PayrollCol.EMPLOYMENT_STATUS),
        pl.first(PayrollCol.SCENARIO_FAMILY).alias(PayrollCol.SCENARIO_FAMILY),
        pl.len().alias(PayrollCol.SHIFT_COUNT),
        pl.sum(PayrollCol.IS_ANOMALY).alias(PayrollCol.ANOMALOUS_SHIFT_COUNT),
        pl.sum(PayrollCol.SCHEDULED_HOURS).alias(PayrollCol.TOTAL_SCHEDULED_HOURS),
        pl.sum(PayrollCol.WORKED_HOURS).alias(PayrollCol.TOTAL_WORKED_HOURS),
        pl.sum(PayrollCol.PAID_HOURS).alias(PayrollCol.TOTAL_PAID_HOURS),
        pl.sum(PayrollCol.REGULAR_HOURS).alias(PayrollCol.TOTAL_REGULAR_HOURS),
        pl.sum(PayrollCol.OVERTIME_HOURS).alias(PayrollCol.TOTAL_OVERTIME_HOURS),
        pl.sum(PayrollCol.EXPECTED_SHIFT_GROSS_PAY).alias(
            PayrollCol.TOTAL_EXPECTED_GROSS_PAY,
        ),
        pl.sum(PayrollCol.PREMIUM_PAY).alias(PayrollCol.TOTAL_PREMIUM_PAY),
        pl.sum(PayrollCol.GROSS_PAY).alias(PayrollCol.TOTAL_GROSS_PAY),
        pl.sum(PayrollCol.DEDUCTIONS).alias(PayrollCol.TOTAL_DEDUCTIONS),
        pl.sum(PayrollCol.NET_PAY).alias(PayrollCol.TOTAL_NET_PAY),
        pl.max(PayrollCol.IS_ANOMALY).alias(PayrollCol.IS_ANOMALY),
        pl.sum(PayrollCol.ANOMALY_DOLLARS).alias(PayrollCol.ANOMALY_DOLLARS),
        pl.max(PayrollCol.OBSERVED_CORRECTION).alias(PayrollCol.OBSERVED_CORRECTION),
        pl.sum(PayrollCol.OBSERVED_CORRECTION_DOLLARS).alias(
            PayrollCol.OBSERVED_CORRECTION_DOLLARS,
        ),
    )
    return (
        cycles.join(
            dominant_category,
            on=[
                PayrollCol.EMPLOYEE_ID,
                PayrollCol.FACILITY_ID,
                PayrollCol.PAY_PERIOD_INDEX,
            ],
            how="left",
        )
        .with_columns(
            pl.concat_str(
                [
                    pl.col(PayrollCol.FACILITY_ID),
                    pl.lit("-"),
                    pl.col(PayrollCol.EMPLOYEE_ID),
                    pl.lit("-PP-"),
                    pl.col(PayrollCol.PAY_PERIOD_INDEX).cast(pl.String),
                ],
            ).alias(PayrollCol.EMPLOYEE_PAY_CYCLE_ID),
            pl.when(pl.col(PayrollCol.IS_ANOMALY) == 1)
            .then(
                pl.col("dominant_anomaly_category").fill_null(
                    SNFAnomalyCategory.NORMAL,
                ),
            )
            .otherwise(pl.lit(SNFAnomalyCategory.NORMAL))
            .alias(PayrollCol.ANOMALY_CATEGORY),
        )
        .drop("dominant_anomaly_category")
        .sort([PayrollCol.EMPLOYEE_ID, PayrollCol.PAY_PERIOD_INDEX])
    )


def employee_pay_cycle_labels(employee_cycles: pl.DataFrame) -> pl.DataFrame:
    return employee_cycles.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).select(
        PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
        PayrollCol.EMPLOYEE_ID,
        PayrollCol.FACILITY_ID,
        PayrollCol.PAY_PERIOD_INDEX,
        PayrollCol.IS_ANOMALY,
        PayrollCol.ANOMALY_CATEGORY,
        PayrollCol.ANOMALY_DOLLARS,
        PayrollCol.SCENARIO_FAMILY,
    )


def scenario_summary(
    payroll: pl.DataFrame,
    scenario: str = "default",
    subgroup_dimension: str = PayrollCol.FACILITY_ID,
) -> pl.DataFrame:
    anomalies = payroll.filter(pl.col(PayrollCol.IS_ANOMALY) == 1)
    total_anomalies = anomalies.height
    total_dollars = float(
        payroll.select(pl.sum(PayrollCol.ANOMALY_DOLLARS)).item() or 0.0,
    )
    rows: list[dict[str, object]] = [
        {
            "scenario": scenario,
            "scope": "overall",
            "subgroup_dimension": "all",
            "subgroup": "all",
            PayrollCol.PAY_PERIOD_INDEX: None,
            "records": payroll.height,
            "anomalies": total_anomalies,
            "anomaly_rate": total_anomalies / max(payroll.height, 1),
            "anomaly_dollars": total_dollars,
            "anomaly_share": 1.0 if total_anomalies else 0.0,
        },
    ]
    if subgroup_dimension in payroll.columns:
        grouped = payroll.group_by(subgroup_dimension).agg(
            pl.len().alias("records"),
            pl.sum(PayrollCol.IS_ANOMALY).alias("anomalies"),
            pl.sum(PayrollCol.ANOMALY_DOLLARS).alias("anomaly_dollars"),
        )
        for row in grouped.to_dicts():
            anomalies_count = int(row["anomalies"] or 0)
            rows.append(
                {
                    "scenario": scenario,
                    "scope": "subgroup",
                    "subgroup_dimension": subgroup_dimension,
                    "subgroup": str(row[subgroup_dimension]),
                    PayrollCol.PAY_PERIOD_INDEX: None,
                    "records": row["records"],
                    "anomalies": anomalies_count,
                    "anomaly_rate": anomalies_count / max(float(row["records"]), 1.0),
                    "anomaly_dollars": float(row["anomaly_dollars"] or 0.0),
                    "anomaly_share": anomalies_count / max(total_anomalies, 1),
                },
            )
    mix = payroll.group_by(PayrollCol.ANOMALY_CATEGORY).agg(
        pl.len().alias("records"),
        pl.sum(PayrollCol.IS_ANOMALY).alias("anomalies"),
        pl.sum(PayrollCol.ANOMALY_DOLLARS).alias("anomaly_dollars"),
    )
    for row in mix.to_dicts():
        rows.append(
            {
                "scenario": scenario,
                "scope": "category",
                "subgroup_dimension": PayrollCol.ANOMALY_CATEGORY,
                "subgroup": str(row[PayrollCol.ANOMALY_CATEGORY]),
                PayrollCol.PAY_PERIOD_INDEX: None,
                "records": row["records"],
                "anomalies": int(row["anomalies"] or 0),
                "anomaly_rate": float(row["anomalies"] or 0)
                / max(float(row["records"]), 1.0),
                "anomaly_dollars": float(row["anomaly_dollars"] or 0.0),
                "anomaly_share": float(row["anomalies"] or 0) / max(total_anomalies, 1),
            },
        )
    return pl.DataFrame(rows, infer_schema_length=None)


def scenario_sanity_summary(
    scenarios: dict[str, pl.DataFrame] | list[tuple[str, pl.DataFrame]] | pl.DataFrame,
    scenario: str = "default",
    score_thresholds: tuple[float, ...] = (),
) -> pl.DataFrame:
    if isinstance(scenarios, pl.DataFrame):
        score_col = "final_anomaly_score"
        category_mix = (
            scenarios.group_by(PayrollCol.ANOMALY_CATEGORY)
            .agg(pl.len().alias("count"))
            .sort(PayrollCol.ANOMALY_CATEGORY)
        )
        row: dict[str, object] = {
            "scenario": scenario,
            "row_count": scenarios.height,
            "anomaly_count": scenarios.filter(
                pl.col(PayrollCol.IS_ANOMALY) == 1,
            ).height,
            "anomaly_dollars": float(
                scenarios.select(pl.sum(PayrollCol.ANOMALY_DOLLARS)).item() or 0.0,
            ),
            "score_p50": float(
                scenarios.select(pl.col(score_col).quantile(0.50)).item() or 0.0,
            ),
            "score_p90": float(
                scenarios.select(pl.col(score_col).quantile(0.90)).item() or 0.0,
            ),
            "category_mix": ";".join(
                f"{item[PayrollCol.ANOMALY_CATEGORY]}={item['count']}"
                for item in category_mix.to_dicts()
            ),
            "max_subgroup_period_anomaly_share": _max_subgroup_period_anomaly_share(
                scenarios,
            ),
            "zero_threshold_candidates": _first_zero_candidate_threshold(
                scenarios,
                score_col,
                score_thresholds,
            ),
            "sparse_condition": "none" if scenarios.height else "empty",
        }
        for threshold in score_thresholds:
            row[f"candidates_at_{threshold:.2f}"] = scenarios.filter(
                pl.col(score_col) >= threshold,
            ).height
        return pl.DataFrame([row], infer_schema_length=None)
    items = scenarios.items() if isinstance(scenarios, dict) else scenarios
    frames = [scenario_summary(frame, name) for name, frame in items]
    return pl.concat(frames, how="diagonal") if frames else pl.DataFrame()


def _max_subgroup_period_anomaly_share(scenarios: pl.DataFrame) -> float:
    if PayrollCol.FACILITY_ID not in scenarios.columns:
        return 0.0
    grouped = scenarios.group_by(
        [PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX],
    ).agg(
        pl.sum(PayrollCol.IS_ANOMALY).alias("anomalies"),
    )
    total = float(scenarios.select(pl.sum(PayrollCol.IS_ANOMALY)).item() or 0.0)
    if total <= 0:
        return 0.0
    return float(grouped.select(pl.max("anomalies") / total).item() or 0.0)


def _first_zero_candidate_threshold(
    scenarios: pl.DataFrame,
    score_col: str,
    score_thresholds: tuple[float, ...],
) -> str:
    for threshold in score_thresholds:
        if scenarios.filter(pl.col(score_col) >= threshold).height == 0:
            return f"{threshold:.2f}"
    return f"{max(score_thresholds):.2f}" if score_thresholds else "none"


def _role_level(role: SNFRole) -> int:
    return {
        SNFRole.CNA: 1,
        SNFRole.DIETARY: 1,
        SNFRole.HOUSEKEEPING: 1,
        SNFRole.MED_AIDE: 2,
        SNFRole.LPN: 3,
        SNFRole.MAINTENANCE: 3,
        SNFRole.RN: 4,
        SNFRole.THERAPY: 4,
        SNFRole.ADMIN: 4,
    }[role]


def _role_shift_probabilities(role: SNFRole) -> np.ndarray:
    if role in {SNFRole.RN, SNFRole.LPN, SNFRole.CNA, SNFRole.MED_AIDE}:
        return np.array([0.43, 0.31, 0.26])
    return np.array([0.76, 0.18, 0.06])


def _add_fatigue_context(
    timed: pl.DataFrame,
    policy: SNFPayPolicyConfig,
) -> pl.DataFrame:
    return timed.sort(
        [PayrollCol.EMPLOYEE_ID, PayrollCol.SHIFT_DATE, PayrollCol.SHIFT_START_HOUR],
    ).with_columns(
        pl.len()
        .over([PayrollCol.EMPLOYEE_ID, PayrollCol.SHIFT_DATE])
        .alias(PayrollCol.SAME_DAY_SHIFT_COUNT),
        (
            (
                pl.col(PayrollCol.SHIFT_DATE).cast(pl.Datetime)
                - pl.col(PayrollCol.SHIFT_DATE)
                .shift(1)
                .over(PayrollCol.EMPLOYEE_ID)
                .cast(pl.Datetime)
            ).dt.total_hours()
            - pl.col(PayrollCol.SCHEDULED_HOURS)
            .shift(1)
            .over(PayrollCol.EMPLOYEE_ID)
            .fill_null(8)
        )
        .fill_null(24.0)
        .clip(0, None)
        .alias(PayrollCol.REST_GAP_HOURS),
        pl.when(
            pl.col(PayrollCol.SHIFT_DATE)
            .diff()
            .over(PayrollCol.EMPLOYEE_ID)
            .dt.total_days()
            == 1,
        )
        .then(1)
        .otherwise(0)
        .cum_sum()
        .over(PayrollCol.EMPLOYEE_ID)
        .alias(PayrollCol.CONSECUTIVE_WORKED_DAYS),
    )


def _is_weekend(value: date) -> bool:
    return value.weekday() >= 5


def _shift_diff_rate(shift_type: ShiftType, policy: SNFPayPolicyConfig) -> float:
    if shift_type == ShiftType.EVENING:
        return policy.evening_diff_rate
    if shift_type == ShiftType.NIGHT:
        return policy.night_diff_rate
    if shift_type == ShiftType.DOUBLE:
        return policy.evening_diff_rate
    return 0.0


def _primary_pay_code_category(
    overtime_hours: float,
    premium_pay: float,
    shift_type: ShiftType,
    is_weekend: bool,
) -> PayCodeCategory:
    if overtime_hours > 0:
        return PayCodeCategory.OVERTIME
    if is_weekend:
        return PayCodeCategory.WEEKEND_DIFF
    if premium_pay > 0 and shift_type in {
        ShiftType.EVENING,
        ShiftType.NIGHT,
        ShiftType.DOUBLE,
    }:
        return PayCodeCategory.SHIFT_DIFF
    return PayCodeCategory.REGULAR


def _pay_code(
    category: PayCodeCategory,
    shift_type: ShiftType,
    is_weekend: bool,
) -> str:
    if category == PayCodeCategory.OVERTIME:
        return "SNF_OT"
    if category == PayCodeCategory.WEEKEND_DIFF:
        return "SNF_WKND"
    if category == PayCodeCategory.SHIFT_DIFF:
        return "SNF_NDIFF" if shift_type == ShiftType.NIGHT else "SNF_EDIFF"
    return "SNF_REG"


def _late_pay_code_rate(row: dict[str, object]) -> float:
    period = _row_int(row, PayrollCol.PAY_PERIOD_INDEX)
    if period < 9:
        return 0.0
    return min(0.05 + (period - 9) * 0.015, 0.12)


def _employment_status(row: dict[str, Any]) -> str:
    termination = row.get(PayrollCol.TERMINATION_DATE)
    if termination is not None and row[PayrollCol.SHIFT_DATE] > termination:
        return "terminated"
    return "active"


def _scenario_family(scenario: ScenarioSpec | None) -> ScenarioFamily:
    if scenario is None:
        return ScenarioFamily.OVERTIME_STAFFING_PRESSURE
    value = (
        scenario.metadata.get("scenario_family")
        or scenario.metadata.get("regime")
        or scenario.name
    )
    text = str(value).replace("-", "_")
    if "premium" in text or "differential" in text:
        return ScenarioFamily.PREMIUM_MISMATCH
    if "baseline" in text:
        return ScenarioFamily.BASELINE
    return ScenarioFamily.OVERTIME_STAFFING_PRESSURE


def _scenario_target_count(
    scenario: ScenarioSpec | None,
    rows: list[dict[str, object]],
) -> int:
    if (
        scenario is not None
        and scenario.anomaly_plan is not None
        and scenario.anomaly_plan.target_count is not None
    ):
        return min(scenario.anomaly_plan.target_count, len(rows))
    return min(max(40, len(rows) // 90), max(len(rows) // 10, 1))


def _scenario_candidates(
    rows: list[dict[str, object]],
    family: ScenarioFamily,
) -> list[int]:
    if family == ScenarioFamily.PREMIUM_MISMATCH:
        return [
            idx
            for idx, row in enumerate(rows)
            if _row_float(row, PayrollCol.PREMIUM_PAY) > 0
        ]
    return [
        idx
        for idx, row in enumerate(rows)
        if _row_float(row, PayrollCol.PAID_HOURS) >= 8
    ]


def _inject_overtime_pressure(
    row: dict[str, object],
    policy: SNFPayPolicyConfig,
    rng: np.random.Generator,
) -> SNFAnomalyCategory:
    original_gross = _row_float(row, PayrollCol.GROSS_PAY)
    row[PayrollCol.SHIFT_TYPE] = ShiftType.DOUBLE
    row[PayrollCol.SCHEDULED_HOURS] = max(
        _row_float(row, PayrollCol.SCHEDULED_HOURS),
        16.0,
    )
    row[PayrollCol.WORKED_HOURS] = round(rng.uniform(15.5, 18.0), 2)
    row[PayrollCol.PAID_HOURS] = row[PayrollCol.WORKED_HOURS]
    row[PayrollCol.REGULAR_HOURS] = policy.overtime_daily_hours
    row[PayrollCol.OVERTIME_HOURS] = round(
        _row_float(row, PayrollCol.PAID_HOURS) - policy.overtime_daily_hours,
        2,
    )
    row[PayrollCol.REST_GAP_HOURS] = round(rng.uniform(2.0, 6.0), 2)
    base = _row_float(row, PayrollCol.BASE_RATE)
    premium = _row_float(row, PayrollCol.PREMIUM_PAY)
    gross = (
        policy.overtime_daily_hours * base
        + _row_float(row, PayrollCol.OVERTIME_HOURS) * base * policy.overtime_multiplier
        + premium
    )
    row[PayrollCol.GROSS_PAY] = round(gross, 2)
    row[PayrollCol.NET_PAY] = round(gross - _row_float(row, PayrollCol.DEDUCTIONS), 2)
    row[PayrollCol.ANOMALY_DOLLARS] = round(abs(gross - original_gross), 2)
    return SNFAnomalyCategory.OVERTIME_DOUBLE_SHIFT


def _inject_premium_mismatch(
    row: dict[str, object],
    policy: SNFPayPolicyConfig,
    rng: np.random.Generator,
) -> SNFAnomalyCategory:
    original_gross = _row_float(row, PayrollCol.GROSS_PAY)
    paid_hours = _row_float(row, PayrollCol.PAID_HOURS)
    premium_add = paid_hours * float(
        rng.choice(
            [
                policy.evening_diff_rate,
                policy.night_diff_rate,
                policy.weekend_diff_rate,
            ],
        ),
    )
    row[PayrollCol.SHIFT_TYPE] = ShiftType.DAY
    row[PayrollCol.IS_WEEKEND] = 0
    row[PayrollCol.PAY_CODE] = "SNF_NDIFF"
    row[PayrollCol.PAY_CODE_CATEGORY] = PayCodeCategory.SHIFT_DIFF
    row[PayrollCol.PREMIUM_PAY] = round(
        _row_float(row, PayrollCol.PREMIUM_PAY) + premium_add,
        2,
    )
    row[PayrollCol.GROSS_PAY] = round(original_gross + premium_add, 2)
    row[PayrollCol.NET_PAY] = round(
        _row_float(row, PayrollCol.NET_PAY) + premium_add,
        2,
    )
    row[PayrollCol.ANOMALY_DOLLARS] = round(premium_add, 2)
    return SNFAnomalyCategory.UNSUPPORTED_SHIFT_DIFFERENTIAL


def _validate_rollups(payroll: pl.DataFrame, rollups: pl.DataFrame) -> None:
    expected = payroll.group_by(
        [PayrollCol.PAY_PERIOD_INDEX, PayrollCol.FACILITY_ID],
    ).agg(
        pl.sum(PayrollCol.GROSS_PAY).round(2).alias("gross"),
        pl.sum(PayrollCol.PAID_HOURS).round(2).alias("hours"),
    )
    actual = rollups.select(
        PayrollCol.PAY_PERIOD_INDEX,
        PayrollCol.FACILITY_ID,
        pl.col("total_gross_pay").round(2).alias("gross"),
        pl.col("total_paid_hours").round(2).alias("hours"),
    )
    if not expected.sort(expected.columns).equals(actual.sort(actual.columns)):
        raise ValueError(
            "facility rollups do not reconcile to shift-level payroll lines",
        )


def _row_float(row: dict[str, object], column: str) -> float:
    value = row[column]
    return float(cast(float | int | str, value))


def _row_int(row: dict[str, object], column: str) -> int:
    value = row[column]
    return int(cast(int | str, value))


def _simulate_observed_corrections(
    payroll: pl.DataFrame,
    rng: np.random.Generator,
) -> pl.DataFrame:
    review_probability = (
        pl.when(pl.col(PayrollCol.IS_ANOMALY) == 0)
        .then(0.01)
        .when(pl.col(PayrollCol.ANOMALY_DOLLARS) >= 140.0)
        .then(0.72)
        .when(pl.col(PayrollCol.ANOMALY_DOLLARS) >= 80.0)
        .then(0.55)
        .when(pl.col(PayrollCol.MANUAL_EDIT) == 1)
        .then(0.48)
        .when(pl.col(PayrollCol.PAYROLL_MATURITY) == "low")
        .then(0.38)
        .otherwise(0.24)
    )
    sampled_review = pl.Series(
        "_observed_review_draw",
        rng.random(payroll.height),
    )
    # Historical corrections are a biased subset: large-dollar, manual-edit, and
    # low-maturity anomalies are more likely to be reviewed and corrected.
    return (
        payroll.with_columns(sampled_review)
        .with_columns(
            review_probability.alias("_observed_review_probability"),
        )
        .with_columns(
            (
                (pl.col(PayrollCol.IS_ANOMALY) == 1)
                & (
                    pl.col("_observed_review_draw")
                    <= pl.col("_observed_review_probability")
                )
            )
            .cast(pl.Int8)
            .alias(PayrollCol.OBSERVED_CORRECTION),
        )
        .with_columns(
            (
                pl.col(PayrollCol.OBSERVED_CORRECTION)
                * pl.col(PayrollCol.ANOMALY_DOLLARS)
            ).alias(PayrollCol.OBSERVED_CORRECTION_DOLLARS),
        )
        .drop("_observed_review_draw", "_observed_review_probability")
    )
