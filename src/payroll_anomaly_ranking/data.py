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
from payroll_anomaly_ranking.scenarios import (
    AnomalyPlan,
    ChangePointEvent,
    DriftPlan,
    ScenarioGeneratorControls,
    ScenarioSpec,
    TargetedAnomalyControl,
)


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

BASELINE_RESIDUAL_FAMILY_WEIGHTS: tuple[tuple[SNFAnomalyCategory, float], ...] = (
    (SNFAnomalyCategory.PAID_VS_SCHEDULED_MISMATCH, 0.32),
    (SNFAnomalyCategory.DUPLICATE_PREMIUM, 0.14),
    (SNFAnomalyCategory.UNSUPPORTED_SHIFT_DIFFERENTIAL, 0.18),
    (SNFAnomalyCategory.CROSS_FACILITY_ALLOCATION, 0.16),
    (SNFAnomalyCategory.RETRO_RATE_MISMATCH, 0.12),
    (SNFAnomalyCategory.OVERTIME_DOUBLE_SHIFT, 0.08),
)

SEVERE_RESIDUAL_CATEGORIES: tuple[str, ...] = (
    str(SNFAnomalyCategory.OVERTIME_DOUBLE_SHIFT),
    str(SNFAnomalyCategory.RETRO_RATE_MISMATCH),
)

MATERIAL_RESIDUAL_CATEGORIES: tuple[str, ...] = (
    str(SNFAnomalyCategory.CROSS_FACILITY_ALLOCATION),
    str(SNFAnomalyCategory.UNSUPPORTED_SHIFT_DIFFERENTIAL),
)


def generate_payroll(
    config: PayrollConfig = PayrollConfig(),
    scenario: ScenarioSpec | None = None,
) -> GeneratedPayroll:
    policy = SNFPayPolicyConfig()
    validate_snf_config(config, policy)
    _validate_supported_scenario_controls(scenario)
    rng = np.random.default_rng(config.seed + (scenario.seed_offset if scenario else 0))
    facilities = generate_facilities(config, rng, scenario=scenario)
    employees = generate_employees(config, facilities, rng, scenario=scenario)
    schedules = generate_schedules(config, facilities, employees, rng)
    timeclock = generate_timeclock(schedules, facilities, config, policy, rng, scenario)
    payroll = generate_payroll_lines(timeclock, policy, rng)
    payroll = apply_scenario_perturbations(payroll, scenario)
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
        metadata={
            **scenario_metadata(scenario),
            "seed": config.seed + (scenario.seed_offset if scenario else 0),
        },
    )


def generate_facilities(
    config: PayrollConfig,
    rng: np.random.Generator,
    scenario: ScenarioSpec | None = None,
) -> pl.DataFrame:
    controls = _scenario_generator_controls(scenario)
    regions = np.array(["Midwest", "Northeast", "Southeast", "West"])
    size_tiers = np.array(["small", "mid", "large"])
    maturities = np.array(["low", "medium", "high"])
    rows: list[dict[str, object]] = []
    for idx in range(1, config.facility_count + 1):
        size = str(rng.choice(size_tiers, p=[0.25, 0.50, 0.25]))
        maturity = str(rng.choice(maturities, p=[0.20, 0.55, 0.25]))
        pressure_base = {"small": 0.95, "mid": 1.0, "large": 1.08}[size]
        pressure = float(
            np.clip(
                rng.normal(
                    pressure_base,
                    0.12 * controls.facility_heterogeneity_multiplier,
                ),
                0.55,
                1.65,
            ),
        )
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
    scenario: ScenarioSpec | None = None,
) -> pl.DataFrame:
    validate_snf_config(config)
    rng = rng or np.random.default_rng(config.seed)
    if facilities is None:
        facilities = generate_facilities(config, rng, scenario=scenario)
    controls = _scenario_generator_controls(scenario)
    facility_profiles = {
        str(row[PayrollCol.FACILITY_ID]): row
        for row in facilities.select(
            PayrollCol.FACILITY_ID,
            PayrollCol.PAYROLL_MATURITY,
            PayrollCol.STAFFING_PRESSURE,
        ).to_dicts()
    }
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
        facility_id = str(rng.choice(facility_ids))
        facility_profile = facility_profiles[facility_id]
        adjusted_mean_rate = mean_rate * _facility_rate_multiplier(
            facility_profile,
            controls,
        )
        base_rate = float(
            np.clip(
                rng.normal(
                    adjusted_mean_rate,
                    sd_rate * controls.base_rate_variation_multiplier,
                ),
                14.0,
                75.0,
            ),
        )
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
    return pl.DataFrame(
        rows,
        schema_overrides={
            PayrollCol.HIRE_DATE: pl.Date,
            PayrollCol.TERMINATION_DATE: pl.Date,
        },
    )


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
            valid_days = [
                day
                for day in range(14)
                if _day_within_employment_window(
                    pay_period_start + timedelta(days=day),
                    cast(date, emp[PayrollCol.HIRE_DATE]),
                    cast(date | None, emp[PayrollCol.TERMINATION_DATE]),
                )
            ]
            if not valid_days:
                continue
            days = rng.choice(
                np.array(valid_days),
                size=min(shift_count, len(valid_days)),
                replace=shift_count > len(valid_days),
            )
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
    scenario: ScenarioSpec | None = None,
) -> pl.DataFrame:
    controls = _scenario_generator_controls(scenario)
    rows = schedules.to_dicts()
    for row in rows:
        maturity = str(row[PayrollCol.PAYROLL_MATURITY])
        pressure = float(row[PayrollCol.STAFFING_PRESSURE])
        missed_rate = min(
            {"low": 0.060, "medium": 0.035, "high": 0.018}[maturity]
            * controls.timekeeping_noise_multiplier,
            0.28,
        )
        manual_rate = min(
            {"low": 0.090, "medium": 0.055, "high": 0.025}[maturity]
            * controls.timekeeping_noise_multiplier,
            0.35,
        )
        scheduled = float(row[PayrollCol.SCHEDULED_HOURS])
        clock_in_variance = rng.normal(0, 9 + pressure * 2)
        clock_out_variance = rng.normal(0, 10 + pressure * 3)
        worked_hours = max(
            0.0,
            scheduled + (clock_out_variance - clock_in_variance) / 60,
        )
        if rng.random() < min(
            0.045 * pressure * controls.timekeeping_noise_multiplier,
            0.20,
        ):
            worked_hours += rng.uniform(1.0, 4.0)
        if rng.random() < min(
            0.018 * pressure * controls.timekeeping_noise_multiplier,
            0.08,
        ):
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
    anomaly_plan = _scenario_anomaly_plan(scenario)
    labels: list[dict[str, object]] = []
    used_indices: set[int] = set()
    targeted_count = _apply_targeted_anomaly_controls(
        rows,
        used_indices,
        labels,
        scenario,
        family,
        policy,
        rng,
    )
    target_count = max(target_count - targeted_count, 0)
    if family == ScenarioFamily.BASELINE and _scenario_label_override(scenario) is None:
        for category, count in _baseline_anomaly_plan(target_count, rng, anomaly_plan):
            candidates = [
                idx
                for idx in _anomaly_candidates(rows, category)
                if idx not in used_indices
            ]
            if not candidates:
                continue
            selected = rng.choice(
                candidates,
                min(count, len(candidates)),
                replace=False,
            )
            for raw_idx in selected:
                idx = int(raw_idx)
                used_indices.add(idx)
                row = rows[idx]
                _apply_shift_anomaly(row, category, family, policy, rng)
                _apply_scenario_anomaly_scaling(row, category, scenario)
                labels.append(_anomaly_label_row(row, family))
                rows[idx] = row
    else:
        category = _scenario_default_category(family)
        label_override = _scenario_label_override(scenario)
        candidates = _scenario_candidates(rows, family)
        if not candidates:
            candidates = list(range(len(rows)))
        selected = rng.choice(
            candidates,
            min(target_count, len(candidates)),
            replace=False,
        )
        for raw_idx in selected:
            idx = int(raw_idx)
            row = rows[idx]
            _apply_shift_anomaly(row, category, family, policy, rng)
            _apply_scenario_anomaly_scaling(row, category, scenario)
            if label_override is not None:
                row[PayrollCol.ANOMALY_CATEGORY] = label_override
            labels.append(_anomaly_label_row(row, family))
            rows[idx] = row
    updated = pl.DataFrame(rows, infer_schema_length=None).with_columns(
        pl.col(PayrollCol.ANOMALY_CATEGORY).cast(pl.String),
        pl.col(PayrollCol.SCENARIO_FAMILY).fill_null(ScenarioFamily.BASELINE),
        pl.col(PayrollCol.SCENARIO_STATUS).fill_null("baseline"),
    )
    updated = _simulate_observed_corrections(updated, rng, scenario)
    return updated, _label_rows_from_payroll(updated)


def apply_scenario_perturbations(
    payroll: pl.DataFrame,
    scenario: ScenarioSpec | None,
) -> pl.DataFrame:
    if scenario is None:
        return payroll
    updated = payroll
    for drift_plan in scenario.drift_plans:
        updated = _apply_drift_plan(updated, drift_plan)
    for change_point in scenario.change_points:
        updated = _apply_change_point(updated, change_point)
    return updated


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


def _apply_drift_plan(payroll: pl.DataFrame, drift_plan: DriftPlan) -> pl.DataFrame:
    scope = _scenario_scope_expr(
        drift_plan.start_period,
        drift_plan.end_period,
        drift_plan.subgroup_filters,
    )
    updated = payroll
    if drift_plan.overtime_multiplier is not None:
        overtime_delta = pl.col(PayrollCol.OVERTIME_HOURS) * (
            drift_plan.overtime_multiplier - 1.0
        )
        gross_delta = (
            overtime_delta
            * pl.col(PayrollCol.PAY_RATE)
            * pl.col(PayrollCol.RATE_MULTIPLIER)
        )
        updated = updated.with_columns(
            pl.when(scope)
            .then(
                (
                    pl.col(PayrollCol.OVERTIME_HOURS) * drift_plan.overtime_multiplier
                ).round(
                    2,
                ),
            )
            .otherwise(pl.col(PayrollCol.OVERTIME_HOURS))
            .alias(PayrollCol.OVERTIME_HOURS),
            pl.when(scope)
            .then((pl.col(PayrollCol.PAID_HOURS) + overtime_delta).round(2))
            .otherwise(pl.col(PayrollCol.PAID_HOURS))
            .alias(PayrollCol.PAID_HOURS),
            pl.when(scope)
            .then((pl.col(PayrollCol.GROSS_PAY) + gross_delta).round(2))
            .otherwise(pl.col(PayrollCol.GROSS_PAY))
            .alias(PayrollCol.GROSS_PAY),
            pl.when(scope)
            .then((pl.col(PayrollCol.NET_PAY) + gross_delta).round(2))
            .otherwise(pl.col(PayrollCol.NET_PAY))
            .alias(PayrollCol.NET_PAY),
        )
    if drift_plan.deduction_multiplier is not None:
        updated = updated.with_columns(
            pl.when(scope)
            .then(
                (pl.col(PayrollCol.DEDUCTIONS) * drift_plan.deduction_multiplier).round(
                    2,
                ),
            )
            .otherwise(pl.col(PayrollCol.DEDUCTIONS))
            .alias(PayrollCol.DEDUCTIONS),
        ).with_columns(
            (pl.col(PayrollCol.GROSS_PAY) - pl.col(PayrollCol.DEDUCTIONS))
            .round(2)
            .alias(PayrollCol.NET_PAY),
        )
    if drift_plan.gross_pay_multiplier is not None:
        updated = updated.with_columns(
            pl.when(scope)
            .then(
                (pl.col(PayrollCol.GROSS_PAY) * drift_plan.gross_pay_multiplier).round(
                    2,
                ),
            )
            .otherwise(pl.col(PayrollCol.GROSS_PAY))
            .alias(PayrollCol.GROSS_PAY),
        ).with_columns(
            (pl.col(PayrollCol.GROSS_PAY) - pl.col(PayrollCol.DEDUCTIONS))
            .round(2)
            .alias(PayrollCol.NET_PAY),
        )
    if drift_plan.payroll_total_multiplier is not None:
        updated = updated.with_columns(
            pl.when(scope)
            .then(
                (
                    pl.col(PayrollCol.GROSS_PAY) * drift_plan.payroll_total_multiplier
                ).round(
                    2,
                ),
            )
            .otherwise(pl.col(PayrollCol.GROSS_PAY))
            .alias(PayrollCol.GROSS_PAY),
            pl.when(scope)
            .then(
                (
                    pl.col(PayrollCol.PREMIUM_PAY) * drift_plan.payroll_total_multiplier
                ).round(
                    2,
                ),
            )
            .otherwise(pl.col(PayrollCol.PREMIUM_PAY))
            .alias(PayrollCol.PREMIUM_PAY),
        ).with_columns(
            (pl.col(PayrollCol.GROSS_PAY) - pl.col(PayrollCol.DEDUCTIONS))
            .round(2)
            .alias(PayrollCol.NET_PAY),
        )
    return updated


def _apply_change_point(
    payroll: pl.DataFrame,
    change_point: ChangePointEvent,
) -> pl.DataFrame:
    if change_point.field != PayrollCol.GROSS_PAY or change_point.pay_code is not None:
        raise ValueError(
            "Only gross-pay change points without pay_code overrides are supported",
        )
    scope = _scenario_scope_expr(
        change_point.start_period,
        change_point.end_period,
        change_point.subgroup_filters,
    )
    adjusted_value = (
        pl.col(change_point.field) * change_point.multiplier
        + change_point.additive_shift
    ).round(2)
    updated = payroll.with_columns(
        pl.when(scope)
        .then(adjusted_value)
        .otherwise(pl.col(change_point.field))
        .alias(change_point.field),
    )
    return updated.with_columns(
        (pl.col(PayrollCol.GROSS_PAY) - pl.col(PayrollCol.DEDUCTIONS))
        .round(2)
        .alias(PayrollCol.NET_PAY),
    )


def _scenario_scope_expr(
    start_period: int | None,
    end_period: int | None,
    subgroup_filters: dict[str, object],
) -> pl.Expr:
    scope = pl.lit(True)
    if start_period is not None:
        scope = scope & (pl.col(PayrollCol.PAY_PERIOD_INDEX) >= start_period)
    if end_period is not None:
        scope = scope & (pl.col(PayrollCol.PAY_PERIOD_INDEX) <= end_period)
    for column, value in subgroup_filters.items():
        if isinstance(value, list | tuple | set):
            scope = scope & pl.col(column).is_in(list(value))
        else:
            scope = scope & (pl.col(column) == value)
    return scope


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
    if scenario is None:
        return {
            "name": "default",
            "scenario_family": ScenarioFamily.BASELINE,
            "implemented_scenarios": [
                "baseline-operations",
                "high-timekeeping-noise",
                "high-facility-heterogeneity",
                "heavy-dollar-tail",
                "subtle-residual-issues",
                "biased-historical-corrections",
                "diversified-severe-issues",
                "temporal-payroll-drift",
            ],
            "future_scenarios": {
                key.value: value for key, value in FUTURE_SCENARIOS.items()
            },
            "policy_assumptions": "Synthetic configurable policy; not legal or payroll advice.",
            "controls_applied": False,
        }
    return {
        **scenario.to_metadata(),
        "name": scenario.name,
        "scenario_family": _scenario_family(scenario),
        "future_scenarios": {
            key.value: value for key, value in FUTURE_SCENARIOS.items()
        },
        "policy_assumptions": "Synthetic configurable policy; not legal or payroll advice.",
        "controls_applied": bool(
            scenario.anomaly_plan
            or scenario.drift_plans
            or scenario.change_points
            or scenario.generator_controls,
        ),
    }


def employee_pay_cycle_records(payroll: pl.DataFrame) -> pl.DataFrame:
    critical_cycle_flags = _employee_cycle_hard_rule_flags(payroll)
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
        .join(
            critical_cycle_flags,
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
            pl.col(PayrollCol.CRITICAL_HARD_RULE_FLAG)
            .fill_null(0)
            .cast(pl.Int8)
            .alias(PayrollCol.CRITICAL_HARD_RULE_FLAG),
        )
        .with_columns(
            (pl.col(PayrollCol.CRITICAL_HARD_RULE_FLAG).fill_null(0) == 0)
            .cast(pl.Int8)
            .alias(PayrollCol.RESIDUAL_RECORD),
            (
                (pl.col(PayrollCol.CRITICAL_HARD_RULE_FLAG).fill_null(0) == 0)
                & (pl.col(PayrollCol.IS_ANOMALY) == 1)
            )
            .cast(pl.Int8)
            .alias(PayrollCol.Y_ISSUE),
            pl.when(pl.col(PayrollCol.CRITICAL_HARD_RULE_FLAG).fill_null(0) == 0)
            .then(pl.col(PayrollCol.ANOMALY_DOLLARS))
            .otherwise(0.0)
            .round(2)
            .alias(PayrollCol.Y_DOLLAR),
        )
        .with_columns(
            _employee_cycle_severe_issue_expr().alias(PayrollCol.SEVERE_ISSUE),
            _employee_cycle_rule_missed_severe_issue_expr().alias(
                PayrollCol.RULE_MISSED_SEVERE_ISSUE,
            ),
        )
        .with_columns(
            _employee_cycle_relevance_grade_expr().alias(PayrollCol.RELEVANCE_GRADE),
            _employee_cycle_net_utility_expr().alias(PayrollCol.NET_UTILITY),
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
        PayrollCol.CRITICAL_HARD_RULE_FLAG,
        PayrollCol.RESIDUAL_RECORD,
        PayrollCol.Y_ISSUE,
        PayrollCol.Y_DOLLAR,
        PayrollCol.SEVERE_ISSUE,
        PayrollCol.RULE_MISSED_SEVERE_ISSUE,
        PayrollCol.RELEVANCE_GRADE,
        PayrollCol.NET_UTILITY,
        PayrollCol.SCENARIO_FAMILY,
    )


def _employee_cycle_base_severe_expr() -> pl.Expr:
    return (pl.col(PayrollCol.IS_ANOMALY) == 1) & (
        (pl.col(PayrollCol.ANOMALY_DOLLARS) >= 260.0)
        | (
            pl.col(PayrollCol.ANOMALY_CATEGORY).is_in(SEVERE_RESIDUAL_CATEGORIES)
            & (pl.col(PayrollCol.ANOMALY_DOLLARS) >= 150.0)
        )
        | (
            (
                pl.col(PayrollCol.ANOMALY_CATEGORY)
                == str(SNFAnomalyCategory.CROSS_FACILITY_ALLOCATION)
            )
            & (pl.col(PayrollCol.ANOMALOUS_SHIFT_COUNT) >= 2)
            & (pl.col(PayrollCol.ANOMALY_DOLLARS) >= 90.0)
        )
    )


def _employee_cycle_severe_issue_expr() -> pl.Expr:
    return _employee_cycle_base_severe_expr().cast(pl.Int8)


def _employee_cycle_relevance_grade_expr() -> pl.Expr:
    material_category = pl.col(PayrollCol.ANOMALY_CATEGORY).is_in(
        MATERIAL_RESIDUAL_CATEGORIES,
    )
    return (
        pl.when(pl.col(PayrollCol.Y_ISSUE) == 0)
        .then(0)
        .when(pl.col(PayrollCol.RULE_MISSED_SEVERE_ISSUE) == 1)
        .then(3)
        .when(
            (pl.col(PayrollCol.ANOMALY_DOLLARS) >= 85.0)
            | (pl.col(PayrollCol.ANOMALOUS_SHIFT_COUNT) >= 2)
            | material_category
            | (pl.col(PayrollCol.OBSERVED_CORRECTION) == 1)
            | (pl.col(PayrollCol.TOTAL_OVERTIME_HOURS) >= 12.0),
        )
        .then(2)
        .otherwise(1)
        .cast(pl.Int8)
    )


def _employee_cycle_rule_missed_severe_issue_expr() -> pl.Expr:
    severe_residual_signal = _employee_cycle_base_severe_expr() & (
        pl.col(PayrollCol.CRITICAL_HARD_RULE_FLAG).fill_null(0) == 0
    )
    return severe_residual_signal.cast(pl.Int8)


def _employee_cycle_net_utility_expr() -> pl.Expr:
    review_cost = 18.0
    recovery_rate = 0.65
    recovered_value = pl.max_horizontal(
        pl.col(PayrollCol.Y_DOLLAR) * recovery_rate,
        1.0,
    )
    return (
        pl.when(pl.col(PayrollCol.Y_ISSUE) == 1)
        .then((recovered_value - review_cost).round(2))
        .otherwise(pl.lit(-review_cost).round(2))
        .cast(pl.Float64)
    )


def employee_cycle_hard_rule_funnel(employee_cycles: pl.DataFrame) -> pl.DataFrame:
    stages = [
        {
            "stage": "All payroll records",
            "records": employee_cycles.height,
            "pct_of_total": 1.0,
            "true_issues": int(
                employee_cycles.select(pl.sum(PayrollCol.IS_ANOMALY)).item() or 0,
            ),
            "severe_issues": int(
                employee_cycles.select(pl.sum(PayrollCol.SEVERE_ISSUE)).item() or 0,
            ),
            "dollar_impact": float(
                employee_cycles.select(pl.sum(PayrollCol.ANOMALY_DOLLARS)).item()
                or 0.0,
            ),
        },
    ]
    hard_rule = employee_cycles.filter(pl.col(PayrollCol.CRITICAL_HARD_RULE_FLAG) == 1)
    residual = employee_cycles.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)
    for stage_name, frame, dollar_col, issue_col in [
        (
            "Critical hard-rule flagged",
            hard_rule,
            PayrollCol.ANOMALY_DOLLARS,
            PayrollCol.IS_ANOMALY,
        ),
        (
            "Residual ML universe",
            residual,
            PayrollCol.Y_DOLLAR,
            PayrollCol.Y_ISSUE,
        ),
    ]:
        stages.append(
            {
                "stage": stage_name,
                "records": frame.height,
                "pct_of_total": frame.height / max(employee_cycles.height, 1),
                "true_issues": int(frame.select(pl.sum(issue_col)).item() or 0),
                "severe_issues": int(
                    frame.select(
                        pl.sum(
                            PayrollCol.RULE_MISSED_SEVERE_ISSUE
                            if stage_name == "Residual ML universe"
                            else PayrollCol.SEVERE_ISSUE,
                        ),
                    ).item()
                    or 0,
                ),
                "dollar_impact": float(frame.select(pl.sum(dollar_col)).item() or 0.0),
            },
        )
    return pl.DataFrame(stages)


def employee_cycle_residual_diagnostics(
    employee_cycles: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    residual = employee_cycles.filter(pl.col(PayrollCol.RESIDUAL_RECORD) == 1)
    hard_rule = employee_cycles.filter(pl.col(PayrollCol.CRITICAL_HARD_RULE_FLAG) == 1)
    return {
        "facility_residual_issue_rate": residual.group_by(PayrollCol.FACILITY_ID)
        .agg(
            pl.len().alias("residual_records"),
            pl.sum(PayrollCol.Y_ISSUE).alias("residual_issues"),
            pl.sum(PayrollCol.Y_DOLLAR).alias("residual_dollars"),
        )
        .with_columns(
            (
                pl.col("residual_issues") / pl.col("residual_records").clip(1, None)
            ).alias("residual_issue_rate"),
        )
        .sort("residual_issue_rate", descending=True),
        "facility_cycle_residual_severe_counts": residual.group_by(
            [PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX],
        )
        .agg(
            pl.len().alias("residual_records"),
            pl.sum(PayrollCol.RULE_MISSED_SEVERE_ISSUE).alias("severe_residual_issues"),
        )
        .sort(["severe_residual_issues", "residual_records"], descending=True),
        "residual_dollar_distribution": residual.select(
            PayrollCol.EMPLOYEE_PAY_CYCLE_ID,
            PayrollCol.FACILITY_ID,
            PayrollCol.PAY_PERIOD_INDEX,
            PayrollCol.Y_DOLLAR,
            PayrollCol.RELEVANCE_GRADE,
            PayrollCol.ANOMALY_CATEGORY,
        ).sort(PayrollCol.Y_DOLLAR, descending=True),
        "issue_type_mix": pl.DataFrame(
            [
                {
                    "population": "critical_hard_rule_flagged",
                    PayrollCol.ANOMALY_CATEGORY: category,
                    "records": count,
                }
                for category, count in _category_counts(hard_rule).items()
            ]
            + [
                {
                    "population": "residual_universe",
                    PayrollCol.ANOMALY_CATEGORY: category,
                    "records": count,
                }
                for category, count in _category_counts(residual).items()
            ],
        ).sort(["population", "records"], descending=[False, True]),
        "residual_records_per_facility_cycle": residual.group_by(
            [PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX],
        )
        .agg(pl.len().alias("residual_records"))
        .sort("residual_records", descending=True),
    }


def _employee_cycle_hard_rule_flags(payroll: pl.DataFrame) -> pl.DataFrame:
    policy = SNFPayPolicyConfig()
    return payroll.group_by(
        [PayrollCol.EMPLOYEE_ID, PayrollCol.FACILITY_ID, PayrollCol.PAY_PERIOD_INDEX],
    ).agg(
        pl.max_horizontal(
            (
                (pl.col(PayrollCol.EMPLOYMENT_STATUS) == "terminated")
                & (pl.col(PayrollCol.GROSS_PAY) > 0)
            )
            .cast(pl.Int8)
            .max(),
            pl.struct(
                [
                    PayrollCol.EMPLOYEE_ID,
                    PayrollCol.SHIFT_DATE,
                    PayrollCol.SHIFT_TYPE,
                    PayrollCol.FACILITY_ID,
                    PayrollCol.PAY_CODE,
                    PayrollCol.GROSS_PAY,
                ],
            )
            .is_duplicated()
            .cast(pl.Int8)
            .max(),
            (
                (pl.col(PayrollCol.EMPLOYMENT_STATUS) == "active")
                & (pl.col(PayrollCol.GROSS_PAY) <= 0)
            )
            .cast(pl.Int8)
            .max(),
            (pl.col(PayrollCol.NET_PAY) < 0).cast(pl.Int8).max(),
            (pl.col(PayrollCol.NET_PAY) > pl.col(PayrollCol.GROSS_PAY) * 1.05)
            .cast(pl.Int8)
            .max(),
            (pl.col(PayrollCol.PAID_HOURS) > 24.0).cast(pl.Int8).max(),
            (
                (pl.col(PayrollCol.PAID_HOURS) > 0)
                & (pl.col(PayrollCol.PAY_RATE).fill_null(0.0) <= 0)
            )
            .cast(pl.Int8)
            .max(),
            (
                (pl.col(PayrollCol.WORKED_HOURS) - pl.col(PayrollCol.SCHEDULED_HOURS))
                > policy.paid_vs_scheduled_threshold
            )
            .cast(pl.Int8)
            .max(),
        )
        .cast(pl.Int8)
        .alias(PayrollCol.CRITICAL_HARD_RULE_FLAG),
    )


def _category_counts(frame: pl.DataFrame) -> dict[str, int]:
    if frame.is_empty():
        return {}
    grouped = frame.group_by(PayrollCol.ANOMALY_CATEGORY).len()
    return {
        str(row[PayrollCol.ANOMALY_CATEGORY]): int(row["len"])
        for row in grouped.to_dicts()
    }


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
        return ScenarioFamily.BASELINE
    metadata_value = scenario.metadata.get("scenario_family") or scenario.metadata.get(
        "regime",
    )
    if metadata_value is not None:
        try:
            return ScenarioFamily(str(metadata_value))
        except ValueError:
            return ScenarioFamily.BASELINE
    return ScenarioFamily.BASELINE


def _scenario_label_override(scenario: ScenarioSpec | None) -> str | None:
    if scenario is None or scenario.anomaly_plan is None:
        return None
    if not scenario.anomaly_plan.category_weights:
        return None
    return max(
        scenario.anomaly_plan.category_weights.items(),
        key=lambda item: item[1],
    )[0]


def _scenario_target_count(
    scenario: ScenarioSpec | None,
    rows: list[dict[str, object]],
) -> int:
    controls = _scenario_generator_controls(scenario)
    if (
        scenario is not None
        and scenario.anomaly_plan is not None
        and scenario.anomaly_plan.target_count is not None
    ):
        target = scenario.anomaly_plan.target_count
    else:
        target = min(max(40, len(rows) // 90), max(len(rows) // 10, 1))
    return min(
        max(round(target * controls.residual_target_multiplier), 1),
        len(rows),
    )


def _scenario_candidates(
    rows: list[dict[str, object]],
    family: ScenarioFamily,
) -> list[int]:
    return _anomaly_candidates(rows, _scenario_default_category(family))


def _scenario_default_category(family: ScenarioFamily) -> SNFAnomalyCategory:
    if family == ScenarioFamily.PREMIUM_MISMATCH:
        return SNFAnomalyCategory.UNSUPPORTED_SHIFT_DIFFERENTIAL
    return SNFAnomalyCategory.OVERTIME_DOUBLE_SHIFT


def _baseline_anomaly_plan(
    target_count: int,
    rng: np.random.Generator,
    anomaly_plan: AnomalyPlan | None = None,
) -> list[tuple[SNFAnomalyCategory, int]]:
    configured_weights = (
        anomaly_plan.category_weights if anomaly_plan is not None else {}
    )
    weights = np.array(
        [
            configured_weights.get(str(category), weight)
            for category, weight in BASELINE_RESIDUAL_FAMILY_WEIGHTS
        ],
        dtype=float,
    )
    if float(weights.sum()) <= 0:
        weights = np.array([weight for _, weight in BASELINE_RESIDUAL_FAMILY_WEIGHTS])
    counts = rng.multinomial(target_count, weights / weights.sum())
    return [
        (category, int(count))
        for (category, _), count in zip(
            BASELINE_RESIDUAL_FAMILY_WEIGHTS,
            counts,
            strict=True,
        )
        if count > 0
    ]


def _anomaly_candidates(
    rows: list[dict[str, object]],
    category: SNFAnomalyCategory,
) -> list[int]:
    if category == SNFAnomalyCategory.UNSUPPORTED_SHIFT_DIFFERENTIAL:
        return [
            idx
            for idx, row in enumerate(rows)
            if _row_float(row, PayrollCol.PREMIUM_PAY) > 0
        ]
    if category == SNFAnomalyCategory.OVERTIME_DOUBLE_SHIFT:
        return [
            idx
            for idx, row in enumerate(rows)
            if _row_float(row, PayrollCol.PAID_HOURS) >= 8
        ]
    return [
        idx
        for idx, row in enumerate(rows)
        if _row_float(row, PayrollCol.PAID_HOURS) >= 4
    ]


def _apply_shift_anomaly(
    row: dict[str, object],
    category: SNFAnomalyCategory,
    family: ScenarioFamily,
    policy: SNFPayPolicyConfig,
    rng: np.random.Generator,
) -> None:
    if category == SNFAnomalyCategory.PAID_VS_SCHEDULED_MISMATCH:
        _inject_minor_timekeeping_leakage(row, policy, rng)
    elif category == SNFAnomalyCategory.DUPLICATE_PREMIUM:
        _inject_duplicate_premium_leakage(row, policy, rng)
    elif category == SNFAnomalyCategory.CROSS_FACILITY_ALLOCATION:
        _inject_cross_facility_allocation(row, policy, rng)
    elif category == SNFAnomalyCategory.RETRO_RATE_MISMATCH:
        _inject_retro_rate_mismatch(row, policy, rng)
    elif category == SNFAnomalyCategory.UNSUPPORTED_SHIFT_DIFFERENTIAL:
        _inject_premium_mismatch(row, policy, rng)
    else:
        _inject_overtime_pressure(row, policy, rng)
    row[PayrollCol.IS_ANOMALY] = 1
    row[PayrollCol.ANOMALY_CATEGORY] = category
    row[PayrollCol.SCENARIO_FAMILY] = family
    row[PayrollCol.SCENARIO_STATUS] = "implemented"
    row[PayrollCol.ANOMALY_DOLLARS] = round(
        max(_row_float(row, PayrollCol.ANOMALY_DOLLARS), 0.0),
        2,
    )


def _anomaly_label_row(
    row: dict[str, object],
    family: ScenarioFamily,
) -> dict[str, object]:
    return {
        PayrollCol.RECORD_ID: row[PayrollCol.RECORD_ID],
        PayrollCol.SHIFT_ID: row[PayrollCol.SHIFT_ID],
        PayrollCol.ANOMALY_CATEGORY: row[PayrollCol.ANOMALY_CATEGORY],
        PayrollCol.ANOMALY_DOLLARS: row[PayrollCol.ANOMALY_DOLLARS],
        PayrollCol.SCENARIO_FAMILY: family,
    }


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


def _inject_minor_timekeeping_leakage(
    row: dict[str, object],
    policy: SNFPayPolicyConfig,
    rng: np.random.Generator,
) -> SNFAnomalyCategory:
    original_gross = _row_float(row, PayrollCol.GROSS_PAY)
    scheduled_hours = _row_float(row, PayrollCol.SCHEDULED_HOURS)
    base_rate = _row_float(row, PayrollCol.BASE_RATE)
    premium_rate = _premium_rate_per_paid_hour(row, policy)
    extra_paid_hours = rng.uniform(0.45, 1.35)
    paid_hours = round(scheduled_hours + extra_paid_hours, 2)
    worked_hours = round(max(scheduled_hours - rng.uniform(0.0, 0.35), 0.0), 2)
    row[PayrollCol.MISSED_PUNCH] = 1
    row[PayrollCol.MANUAL_EDIT] = 1
    row[PayrollCol.APPROVAL_STATUS] = ApprovalStatus.MANUAL_OVERRIDE
    row[PayrollCol.WORKED_HOURS] = worked_hours
    row[PayrollCol.PAID_HOURS] = paid_hours
    row[PayrollCol.REGULAR_HOURS] = round(
        min(paid_hours, policy.overtime_daily_hours),
        2,
    )
    row[PayrollCol.OVERTIME_HOURS] = round(
        max(paid_hours - policy.overtime_daily_hours, 0.0),
        2,
    )
    gross = _gross_pay_from_hours(row, policy, base_rate, premium_rate)
    row[PayrollCol.GROSS_PAY] = gross
    row[PayrollCol.NET_PAY] = round(gross - _row_float(row, PayrollCol.DEDUCTIONS), 2)
    row[PayrollCol.ANOMALY_DOLLARS] = round(max(gross - original_gross, 0.0), 2)
    return SNFAnomalyCategory.PAID_VS_SCHEDULED_MISMATCH


def _inject_duplicate_premium_leakage(
    row: dict[str, object],
    policy: SNFPayPolicyConfig,
    rng: np.random.Generator,
) -> SNFAnomalyCategory:
    original_gross = _row_float(row, PayrollCol.GROSS_PAY)
    duplicate_premium = round(rng.uniform(12.0, 38.0), 2)
    row[PayrollCol.MANUAL_EDIT] = 1
    row[PayrollCol.APPROVAL_STATUS] = ApprovalStatus.MANUAL_OVERRIDE
    row[PayrollCol.PAY_CODE] = "SNF_DUPPREM"
    row[PayrollCol.PAY_CODE_CATEGORY] = PayCodeCategory.SHIFT_DIFF
    row[PayrollCol.PREMIUM_PAY] = round(
        _row_float(row, PayrollCol.PREMIUM_PAY) + duplicate_premium,
        2,
    )
    row[PayrollCol.GROSS_PAY] = round(original_gross + duplicate_premium, 2)
    row[PayrollCol.NET_PAY] = round(
        _row_float(row, PayrollCol.NET_PAY) + duplicate_premium,
        2,
    )
    row[PayrollCol.ANOMALY_DOLLARS] = duplicate_premium
    return SNFAnomalyCategory.DUPLICATE_PREMIUM


def _inject_cross_facility_allocation(
    row: dict[str, object],
    policy: SNFPayPolicyConfig,
    rng: np.random.Generator,
) -> SNFAnomalyCategory:
    original_gross = _row_float(row, PayrollCol.GROSS_PAY)
    premium_rate = _premium_rate_per_paid_hour(row, policy)
    allocation_hours = rng.uniform(1.0, 2.0)
    paid_hours = round(_row_float(row, PayrollCol.PAID_HOURS) + allocation_hours, 2)
    base_rate = _row_float(row, PayrollCol.BASE_RATE)
    home_facility = str(row[PayrollCol.HOME_FACILITY_ID])
    row[PayrollCol.WORKED_FACILITY_ID] = f"FLOAT-{home_facility}"
    row[PayrollCol.MANUAL_EDIT] = 1
    row[PayrollCol.MISSED_PUNCH] = int(rng.random() < 0.35)
    row[PayrollCol.APPROVAL_STATUS] = ApprovalStatus.MANUAL_OVERRIDE
    row[PayrollCol.PAID_HOURS] = paid_hours
    row[PayrollCol.REGULAR_HOURS] = round(
        min(paid_hours, policy.overtime_daily_hours),
        2,
    )
    row[PayrollCol.OVERTIME_HOURS] = round(
        max(paid_hours - policy.overtime_daily_hours, 0.0),
        2,
    )
    gross = _gross_pay_from_hours(row, policy, base_rate, premium_rate)
    row[PayrollCol.GROSS_PAY] = gross
    row[PayrollCol.NET_PAY] = round(gross - _row_float(row, PayrollCol.DEDUCTIONS), 2)
    row[PayrollCol.ANOMALY_DOLLARS] = round(max(gross - original_gross, 25.0), 2)
    return SNFAnomalyCategory.CROSS_FACILITY_ALLOCATION


def _inject_retro_rate_mismatch(
    row: dict[str, object],
    policy: SNFPayPolicyConfig,
    rng: np.random.Generator,
) -> SNFAnomalyCategory:
    original_gross = _row_float(row, PayrollCol.GROSS_PAY)
    base_rate = _row_float(row, PayrollCol.BASE_RATE)
    premium_rate = _premium_rate_per_paid_hour(row, policy)
    rate_multiplier = rng.uniform(1.22, 1.55)
    paid_hours = _row_float(row, PayrollCol.PAID_HOURS)
    overtime_hours = _row_float(row, PayrollCol.OVERTIME_HOURS)
    inflated_rate = round(base_rate * rate_multiplier, 2)
    row[PayrollCol.MANUAL_EDIT] = 1
    row[PayrollCol.APPROVAL_STATUS] = ApprovalStatus.MANUAL_OVERRIDE
    row[PayrollCol.PAY_RATE] = inflated_rate
    row[PayrollCol.MANUAL_ADJUSTMENT] = round(
        (inflated_rate - base_rate) * paid_hours,
        2,
    )
    row[PayrollCol.REGULAR_HOURS] = round(
        min(paid_hours, policy.overtime_daily_hours),
        2,
    )
    row[PayrollCol.OVERTIME_HOURS] = round(overtime_hours, 2)
    regular_hours = _row_float(row, PayrollCol.REGULAR_HOURS)
    gross = round(
        regular_hours * inflated_rate
        + overtime_hours * inflated_rate * policy.overtime_multiplier
        + paid_hours * premium_rate,
        2,
    )
    row[PayrollCol.GROSS_PAY] = gross
    row[PayrollCol.NET_PAY] = round(gross - _row_float(row, PayrollCol.DEDUCTIONS), 2)
    row[PayrollCol.ANOMALY_DOLLARS] = round(max(gross - original_gross, 0.0), 2)
    return SNFAnomalyCategory.RETRO_RATE_MISMATCH


def _premium_rate_per_paid_hour(
    row: dict[str, object],
    policy: SNFPayPolicyConfig,
) -> float:
    shift_type = ShiftType(row[PayrollCol.SHIFT_TYPE])
    return _shift_diff_rate(shift_type, policy) + (
        policy.weekend_diff_rate
        if _is_weekend(cast(date, row[PayrollCol.SHIFT_DATE]))
        else 0.0
    )


def _gross_pay_from_hours(
    row: dict[str, object],
    policy: SNFPayPolicyConfig,
    base_rate: float,
    premium_rate: float,
) -> float:
    regular_hours = _row_float(row, PayrollCol.REGULAR_HOURS)
    overtime_hours = _row_float(row, PayrollCol.OVERTIME_HOURS)
    paid_hours = _row_float(row, PayrollCol.PAID_HOURS)
    return round(
        regular_hours * base_rate
        + overtime_hours * base_rate * policy.overtime_multiplier
        + paid_hours * premium_rate,
        2,
    )


def _scenario_generator_controls(
    scenario: ScenarioSpec | None,
) -> ScenarioGeneratorControls:
    if scenario is None or scenario.generator_controls is None:
        return ScenarioGeneratorControls()
    return scenario.generator_controls


def _scenario_anomaly_plan(scenario: ScenarioSpec | None) -> AnomalyPlan:
    if scenario is None or scenario.anomaly_plan is None:
        return AnomalyPlan()
    return scenario.anomaly_plan


def _validate_supported_scenario_controls(scenario: ScenarioSpec | None) -> None:
    if scenario is None:
        return
    for drift_plan in scenario.drift_plans:
        if drift_plan.pay_code_mix_shift:
            raise ValueError("pay_code_mix_shift is not supported in the active DGP")
        if drift_plan.multiplier_noise != 0.0:
            raise ValueError("multiplier_noise is not supported in the active DGP")
    for change_point in scenario.change_points:
        if change_point.field != PayrollCol.GROSS_PAY:
            raise ValueError(
                "Only gross-pay change points are supported in the active DGP",
            )
        if change_point.pay_code is not None:
            raise ValueError(
                "pay_code overrides are not supported in active change-point events",
            )


def _apply_scenario_anomaly_scaling(
    row: dict[str, object],
    category: SNFAnomalyCategory,
    scenario: ScenarioSpec | None,
    severity_overrides: dict[str, float] | None = None,
) -> None:
    controls = _scenario_generator_controls(scenario)
    anomaly_plan = _scenario_anomaly_plan(scenario)
    severity_multiplier = anomaly_plan.severity_multipliers.get(str(category), 1.0)
    if severity_overrides is not None:
        severity_multiplier *= severity_overrides.get(str(category), 1.0)
    multiplier = controls.anomaly_dollar_multiplier * severity_multiplier
    if multiplier == 1.0:
        return
    anomaly_dollars = round(_row_float(row, PayrollCol.ANOMALY_DOLLARS) * multiplier, 2)
    gross_delta = anomaly_dollars - _row_float(row, PayrollCol.ANOMALY_DOLLARS)
    row[PayrollCol.ANOMALY_DOLLARS] = max(anomaly_dollars, 0.0)
    row[PayrollCol.GROSS_PAY] = round(
        _row_float(row, PayrollCol.GROSS_PAY) + gross_delta,
        2,
    )
    row[PayrollCol.NET_PAY] = round(
        _row_float(row, PayrollCol.NET_PAY) + gross_delta,
        2,
    )


def _apply_targeted_anomaly_controls(
    rows: list[dict[str, object]],
    used_indices: set[int],
    labels: list[dict[str, object]],
    scenario: ScenarioSpec | None,
    family: ScenarioFamily,
    policy: SNFPayPolicyConfig,
    rng: np.random.Generator,
) -> int:
    anomaly_plan = _scenario_anomaly_plan(scenario)
    applied = 0
    for control in anomaly_plan.targeted_controls:
        candidate_indices = [
            idx
            for idx, row in enumerate(rows)
            if idx not in used_indices and _targeted_scope_match(row, control)
        ]
        if not candidate_indices:
            continue
        requested = control.target_count
        if requested is None:
            requested = max(
                1,
                round(len(candidate_indices) * 0.05 * control.propensity_multiplier),
            )
        plan = _targeted_anomaly_plan(
            min(requested, len(candidate_indices)),
            control.category_weights,
            family,
            rng,
        )
        for category_name, category_count in plan:
            category = _resolved_target_category(category_name, family)
            label_override = category_name if str(category) != category_name else None
            available = [idx for idx in candidate_indices if idx not in used_indices]
            if not available:
                continue
            selected = rng.choice(
                available,
                min(category_count, len(available)),
                replace=False,
            )
            for raw_idx in selected:
                idx = int(raw_idx)
                used_indices.add(idx)
                row = rows[idx]
                _apply_shift_anomaly(row, category, family, policy, rng)
                _apply_scenario_anomaly_scaling(
                    row,
                    category,
                    scenario,
                    severity_overrides=control.severity_multipliers,
                )
                if label_override is not None:
                    row[PayrollCol.ANOMALY_CATEGORY] = label_override
                labels.append(_anomaly_label_row(row, family))
                rows[idx] = row
                applied += 1
    return applied


def _targeted_anomaly_plan(
    target_count: int,
    category_weights: dict[str, float],
    family: ScenarioFamily,
    rng: np.random.Generator,
) -> list[tuple[str, int]]:
    if not category_weights:
        return [(str(_scenario_default_category(family)), target_count)]
    names = list(category_weights)
    weights = np.array(list(category_weights.values()), dtype=float)
    if float(weights.sum()) <= 0:
        return [(names[0], target_count)]
    counts = rng.multinomial(target_count, weights / weights.sum())
    return [
        (name, int(count))
        for name, count in zip(names, counts, strict=True)
        if count > 0
    ]


def _targeted_scope_match(
    row: dict[str, object],
    control: TargetedAnomalyControl,
) -> bool:
    period = _row_int(row, PayrollCol.PAY_PERIOD_INDEX)
    if control.start_period is not None and period < control.start_period:
        return False
    if control.end_period is not None and period > control.end_period:
        return False
    for column, value in control.subgroup_filters.items():
        row_value = row.get(column)
        if isinstance(value, list | tuple | set):
            if row_value not in value:
                return False
        elif row_value != value:
            return False
    return True


def _resolved_target_category(
    category_name: str,
    family: ScenarioFamily,
) -> SNFAnomalyCategory:
    try:
        return SNFAnomalyCategory(category_name)
    except ValueError:
        return _scenario_default_category(family)


def _label_rows_from_payroll(payroll: pl.DataFrame) -> pl.DataFrame:
    return payroll.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).select(
        PayrollCol.RECORD_ID,
        PayrollCol.SHIFT_ID,
        PayrollCol.ANOMALY_CATEGORY,
        PayrollCol.ANOMALY_DOLLARS,
        PayrollCol.SCENARIO_FAMILY,
    )


def _day_within_employment_window(
    shift_date: date,
    hire_date: date,
    termination_date: date | None,
) -> bool:
    if shift_date < hire_date:
        return False
    if termination_date is not None and shift_date > termination_date:
        return False
    return True


def _facility_rate_multiplier(
    facility_profile: dict[str, object],
    controls: ScenarioGeneratorControls,
) -> float:
    pressure = float(
        cast(
            float | int | str,
            facility_profile[PayrollCol.STAFFING_PRESSURE],
        ),
    )
    maturity = str(facility_profile[PayrollCol.PAYROLL_MATURITY])
    maturity_multiplier = {"low": 1.04, "medium": 1.0, "high": 0.97}[maturity]
    pressure_multiplier = (
        1.0 + (pressure - 1.0) * 0.30 * controls.facility_heterogeneity_multiplier
    )
    return max(0.85, min(1.25, maturity_multiplier * pressure_multiplier))


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
    scenario: ScenarioSpec | None = None,
) -> pl.DataFrame:
    controls = _scenario_generator_controls(scenario)
    bias_multiplier = controls.observed_review_bias_multiplier
    review_probability = (
        pl.when(pl.col(PayrollCol.IS_ANOMALY) == 0)
        .then(0.01)
        .when(pl.col(PayrollCol.ANOMALY_DOLLARS) >= 140.0)
        .then(min(0.72 * bias_multiplier, 0.98))
        .when(pl.col(PayrollCol.ANOMALY_DOLLARS) >= 80.0)
        .then(min(0.55 * bias_multiplier, 0.94))
        .when(pl.col(PayrollCol.MANUAL_EDIT) == 1)
        .then(min(0.48 * bias_multiplier, 0.90))
        .when(pl.col(PayrollCol.PAYROLL_MATURITY) == "low")
        .then(min(0.38 * bias_multiplier, 0.82))
        .otherwise(min(0.24 * (1 + (bias_multiplier - 1) * 0.35), 0.55))
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
