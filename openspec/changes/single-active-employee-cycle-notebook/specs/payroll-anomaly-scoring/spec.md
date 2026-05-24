## MODIFIED Requirements

### Requirement: Feature engineering notebook walkthrough
The active employee-pay-cycle notebook SHALL demonstrate leakage-safe historical, peer, normalization, and robust statistical features using concrete synthetic employee-pay-cycle payroll records.

#### Scenario: Concrete employee-pay-cycle feature examples are displayed
- **WHEN** the active employee-pay-cycle notebook runs
- **THEN** it displays selected employee-pay-cycle records with total gross pay, expected cycle pay, scheduled, worked, and paid hour context, overtime and premium context, prior rolling baselines, peer baselines, and formulation-relevant feature columns

### Requirement: Leakage-safe feature explanation
The active employee-pay-cycle notebook SHALL explain which features are leakage-safe and why injected labels are retained for evaluation but not used as training or scoring features.

#### Scenario: Leakage-safe narrative is present
- **WHEN** a reviewer reads the feature engineering section of the active employee-pay-cycle notebook
- **THEN** the notebook states that historical features exclude current and future periods and that labels are not used as model features

### Requirement: Baseline scoring comparison inputs
The active employee-pay-cycle notebook SHALL demonstrate classification, regression, expected-value, ranking, ML-only, and final active ranking scores as separate comparison signals using the employee-pay-cycle model comparison outputs.

#### Scenario: Baseline score columns are compared
- **WHEN** the model formulations or ablation sections of the active employee-pay-cycle notebook run
- **THEN** they display classification, regression, expected-value, ranking, ML-only, and final active ranking score columns or summaries and explain what each contributes to payroll review prioritization

### Requirement: Payroll hybrid ranking rationale
The active employee-pay-cycle notebook SHALL explain why payroll review prioritization benefits from comparing multiple formulations and promoting the strongest employee-pay-cycle ranking evidence rather than assuming one preselected method is correct.

#### Scenario: Formulation rationale is included
- **WHEN** a reviewer reads the feature engineering or model formulations sections of the active employee-pay-cycle notebook
- **THEN** the notebook describes why payroll ranking compares multiple leakage-safe formulations, operational context, peer and history context, and expected-value reasoning rather than relying on one unexplained score
