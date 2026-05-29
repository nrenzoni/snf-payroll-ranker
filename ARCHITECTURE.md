# Architecture

This document describes the high-level architecture direction for the payroll ranking library.

## 1. System Context

The active system direction is a production-oriented payroll ranking library whose first phase uses research and validation to determine what is safe and valuable enough to promote into operational use. The primary users are:

- **Data-science and ML engineering users** who need reusable employee-pay-cycle data, feature, model, and evaluation contracts.
- **Operations and product stakeholders** who need evidence that promoted methods are robust enough for later payroll-review workflows.
- **Future application-layer consumers** who may build review queues or operational experiences on top of the validated library.

The active output is not a fraud or misconduct label. It is a reusable employee-pay-cycle ranking and evaluation foundation that can later power review workflows after the research phase promotes production-candidate components.

## 2. Component Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  Data Layer                                                          │
│  ├── Synthetic employee-pay-cycle payroll generation                │
│  └── Validation rules, aggregation checks, schema guards            │
├─────────────────────────────────────────────────────────────────────┤
│  Feature Engineering Layer                                           │
│  ├── Leakage-safe employee and facility history features            │
│  ├── Facility-normalized and peer-relative features                 │
│  ├── Robust distributional features                                 │
│  └── Optional lower-level context features when operationally useful│
├─────────────────────────────────────────────────────────────────────┤
│  Scoring Layer                                                       │
│  ├── Classification interfaces                                      │
│  ├── Regression interfaces                                          │
│  ├── Expected-value scoring interfaces                              │
│  └── Learning-to-rank interfaces                                    │
├─────────────────────────────────────────────────────────────────────┤
│  Uncertainty Layer                                                   │
│  ├── Calibration and reliability diagnostics                        │
│  ├── Prediction interval and uncertainty diagnostics                │
│  ├── Data-quality and out-of-distribution diagnostics               │
│  └── Separate risk and uncertainty outputs                          │
├─────────────────────────────────────────────────────────────────────┤
│  Output Layer                                                        │
│  ├── Grouped ranking metrics and validation artifacts               │
│  ├── Production-candidacy reporting                                 │
│  └── Optional application-layer review queues built later           │
└─────────────────────────────────────────────────────────────────────┘
```

## 3. Data Model

The active modeling grain is **employee-pay-cycle**. Lower-level shift, schedule, and timeclock data may still be generated or engineered as supporting context, but they no longer define the active runtime contract.

Key entities:

| Entity | Key Fields | Purpose |
|--------|-----------|---------|
| **Employee-Pay-Cycle Record** | `record_id`, `employee_id`, `pay_period_index`, aggregated pay and hour fields | Canonical scoring and evaluation row |
| **Supporting Shift Context** | lower-level shift, schedule, or timeclock fields where retained | Optional explanatory or feature context |
| **Employee** | `employee_id`, tenure, employment context | History & peer grouping |
| **Facility** | `facility_id` | Normalization baseline & approval summary grouping |
| **Pay Period** | `pay_period_index` | Temporal split boundaries & leakage guard |

## 4. Scoring Component Design

The active scoring architecture is formulation-oriented rather than tied to one preselected hybrid score. Phase 1 research compares alternative employee-pay-cycle scoring formulations and promotes only methods or method combinations that earn production candidacy.

| Active Formulation | Question It Answers | Example Output |
|-----------|----------|--------------|
| **Classification** | Is this employee-pay-cycle likely review-worthy? | risk probability |
| **Regression** | What is the expected impact or severity? | predicted impact |
| **Expected Value** | What is the expected loss if ignored? | probability × conditional impact |
| **Learning to Rank** | Which employee-pay-cycle rows should be reviewed first within a queue? | group-relative priority score |

## 5. Temporal Safety

Leakage prevention is enforced at multiple layers:

- **Historical features** exclude the current payroll cycle and all future cycles.
- **Peer baselines** are built from scoring-time-available references only.
- **Temporal splits** remain the active default and random row sampling remains a debugging-only anti-pattern.
- **Rolling-origin evaluation** stays aligned with later production retraining cadence.
- **Label isolation** continues to separate evaluation truth from active features and operational outputs.

## 6. Spec-Driven Development

Non-trivial behavior changes follow a propose / apply / archive cycle using an internal OpenSpec-like workflow. Design documents, spec artifacts, and archived changes live under `openspec/`. This ensures that feature additions, scoring changes, and evaluation criteria are traceable and versioned alongside code.

## 7. Deployment Path

*Deployment path: TBD.*

A production implementation would promote validated employee-pay-cycle library components into payroll, facility, feedback, monitoring, and retraining workflows after the Phase 1 research gate. This repository does not implement or claim live integrations.

Monitoring should track exception count per payroll cycle, approval queue yield, confirmed exception rate from feedback, estimated exposure flagged and confirmed, feature drift, score drift, alert concentration by facility/unit/role/shift, latency, data freshness, validation failures, and threshold-baseline drift.
