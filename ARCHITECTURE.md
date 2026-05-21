# Architecture

This document describes the high-level system architecture of the SNF Payroll Anomaly Ranking pipeline.

## 1. System Context

The system targets skilled nursing facility (SNF) weekly payroll approval workflows. The primary users are:

- **Facility administrators / business office managers** who review flagged shift-level records before payroll close.
- **Regional operators** who need pay-period/facility summaries of exception concentration and estimated exposure.
- **Data-science reviewers** who validate method performance, temporal stability, and uncertainty behavior.

The output is not a fraud or misconduct label. It is a ranked pre-approval exception queue with recommended actions, sources to check, and review-safe explanations.

## 2. Component Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  Data Layer                                                          │
│  ├── Synthetic payroll, schedule, timeclock, HR lifecycle records   │
│  └── Validation rules, aggregation checks, schema guards           │
├─────────────────────────────────────────────────────────────────────┤
│  Feature Engineering Layer                                           │
│  ├── History features (lag, rolling median/std, tenure bucket)     │
│  ├── Peer features (facility-role-shift, cross-facility, tenure)   │
│  ├── Robust features (MAD z-score, IQR outlier, percentile)        │
│  └── Premium, fatigue, schedule/timeclock mismatch features          │
├─────────────────────────────────────────────────────────────────────┤
│  Scoring Layer                                                       │
│  ├── Deterministic rule flags & severity score                     │
│  ├── Robust statistical scores (z, MAD, peer deviation)          │
│  ├── Unsupervised outlier detection (Isolation Forest)             │
│  ├── Estimated exposure & dollar-impact score                      │
│  └── Configurable hybrid ranking combining all components            │
├─────────────────────────────────────────────────────────────────────┤
│  Uncertainty Layer                                                   │
│  ├── Ensemble disagreement across score components                   │
│  ├── Bootstrap score intervals                                       │
│  ├── Expected gross-pay intervals                                    │
│  ├── Peer-group & employee-history sample-size uncertainty           │
│  ├── Data-quality & out-of-distribution detection                    │
│  └── Composite uncertainty bucket (Low / Medium / High)            │
├─────────────────────────────────────────────────────────────────────┤
│  Output Layer                                                        │
│  ├── Administrator-safe approval queue                               │
│  ├── Evaluation-labeled review queue (synthetic truth only)          │
│  ├── Facility approval summary (pay-period / facility)               │
│  └── Temporal evaluation metrics (backtest, rolling origin)        │
└─────────────────────────────────────────────────────────────────────┘
```

## 3. Data Model

The modeling grain is **shift-level** rather than employee-pay-period aggregate. Shift context is required to detect overtime, double-shift, rest-gap, schedule/timeclock mismatch, and premium eligibility issues.

Key entities:

| Entity | Key Fields | Purpose |
|--------|-----------|---------|
| **Payroll Record** | `record_id`, `employee_id`, `pay_period_index`, `gross_pay`, `net_pay`, `deductions` | Atomic line for scoring |
| **Shift** | `shift_id`, `shift_date`, `shift_type`, `facility_id`, `unit`, `role`, `pay_code` | Operational context |
| **Employee** | `employee_id`, `tenure_months`, `employment_status`, `license_type` | History & peer grouping |
| **Facility** | `facility_id` | Normalization baseline & approval summary grouping |
| **Pay Period** | `pay_period_index` | Temporal split boundaries & leakage guard |

## 4. Scoring Component Design

The final approval exception score is a **hybrid** rather than a single model output. This reflects the reality that SNF payroll review involves distinct risk types:

| Component | Captures | Example Signal |
|-----------|----------|--------------|
| **Rule Score** | Deterministic compliance violations | Paid hours > scheduled hours, unsupported weekend premium, duplicate premium signature |
| **Statistical Score** | Univariate distributional unusualness | Gross pay MAD z-score, peer gross deviation ratio |
| **Peer Score** | Context-relative unusualness | Cross-facility role-shift median deviation |
| **History Score** | Employee trajectory change | Gross pay % change vs. rolling median |
| **ML Score** | Multivariate unusualness across feature space | Isolation Forest decision function |
| **Dollar / Exposure Score** | Estimated financial impact | Excess over expected pay, premium mismatch dollars, overtime exposure |
| **Schedule/Timeclock Score** | Operational mismatch | Missed punch, manual edit, rest-gap risk, paid-vs-scheduled variance |
| **Premium Eligibility Score** | Policy-context mismatch | Premium pay without eligible shift type, duplicate premiums |

Each component is computed independently and then combined via configurable weights. This makes the system inspectable and lets operators tune sensitivity by risk type.

## 5. Temporal Safety

Leakage prevention is enforced at multiple layers:

- **Historical features** exclude the current pay period and all future periods. Rolling medians, lags, and standard deviations use `shift(1)` and `rolling_*` over prior records only.
- **Peer baselines** are built from prior pay periods only. The scored row is excluded from its own peer aggregate.
- **Temporal splits** divide data by `pay_period_index` rather than random row sampling. Train / validation / test sets are strictly ordered in time.
- **Rolling-origin evaluation** trains on expanding prior windows and scores on the next period, mimicking production retraining cadence.
- **Label isolation**: `is_anomaly`, `anomaly_category`, and `anomaly_dollars` are never used as features or score inputs. They are retained only for evaluation and notebook diagnostics.

## 6. Spec-Driven Development

Non-trivial behavior changes follow a propose / apply / archive cycle using an internal OpenSpec-like workflow. Design documents, spec artifacts, and archived changes live under `openspec/`. This ensures that feature additions, scoring changes, and evaluation criteria are traceable and versioned alongside code.

## 7. Deployment Path

*Deployment path: TBD.*

A production implementation would ingest payroll, schedule, timeclock, HR lifecycle, facility reference, pay policy, and administrator feedback extracts through validation, feature engineering, scoring, pre-approval queue export, monitoring, and retraining workflows. This repository does not implement or claim live integrations.

Monitoring should track exception count per payroll cycle, approval queue yield, confirmed exception rate from feedback, estimated exposure flagged and confirmed, feature drift, score drift, alert concentration by facility/unit/role/shift, latency, data freshness, validation failures, and threshold-baseline drift.
