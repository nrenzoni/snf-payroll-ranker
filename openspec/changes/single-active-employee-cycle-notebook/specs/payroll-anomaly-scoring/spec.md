## MODIFIED Requirements

### Requirement: Feature engineering notebook walkthrough
The active employee-pay-cycle notebook SHALL demonstrate leakage-safe historical, peer, normalization, and robust statistical features using concrete synthetic employee-pay-cycle payroll records from the residual universe after critical hard rules are applied.

#### Scenario: Concrete employee-pay-cycle feature examples are displayed
- **WHEN** the active employee-pay-cycle notebook runs
- **THEN** it displays selected residual employee-pay-cycle records with total gross pay, expected cycle pay, scheduled, worked, and paid hour context, overtime and premium context, prior rolling baselines, peer baselines, and formulation-relevant feature columns

### Requirement: Leakage-safe feature explanation
The active employee-pay-cycle notebook SHALL explain which features are leakage-safe and why injected labels are retained for evaluation but not used as training or scoring features.

#### Scenario: Leakage-safe narrative is present
- **WHEN** a reviewer reads the feature engineering section of the active employee-pay-cycle notebook
- **THEN** the notebook states that historical features exclude current and future periods and that labels are not used as model features
- **AND** it distinguishes critical hard-rule flags, which define the residual universe, from soft warning signals that may remain as ML features
- **AND** it explicitly excludes compliance, PBJ, and HPRD fields from the residual-model feature set

### Requirement: Residual ML formulation comparison inputs
The active employee-pay-cycle notebook SHALL compare only ML formulations on the residual universe using the employee-pay-cycle model comparison outputs.

#### Scenario: Residual ML score columns are compared
- **WHEN** the model formulations or ablation sections of the active employee-pay-cycle notebook run
- **THEN** they display classifier, cost-sensitive classifier, regressor, expected-value, and learning-to-rank score columns or summaries and explain what each contributes to residual payroll review prioritization
- **AND** they describe hard rules as the upstream gate rather than as a competing model in the formulation comparison

### Requirement: Explicit residual ranking labels
The active employee-pay-cycle scoring workflow SHALL define residual labels for formulation training and evaluation without exposing evaluation-only labels as training features or analyst-facing fields where they do not belong.

#### Scenario: Latent residual issue truth is defined
- **WHEN** employee-pay-cycle labels are constructed after the critical hard-rule gate
- **THEN** each residual employee-pay-cycle receives a binary `y_issue` label derived from latent residual issue truth rather than observed historical review outcomes

#### Scenario: Residual dollar target is defined
- **WHEN** employee-pay-cycle labels are constructed after the critical hard-rule gate
- **THEN** each residual employee-pay-cycle receives a `y_dollar` label representing residual financial impact for regression-style formulations

#### Scenario: Relevance grade is deterministic and documented
- **WHEN** employee-pay-cycle labels are constructed from synthetic latent anomalies
- **THEN** each residual employee-pay-cycle receives a deterministic `relevance_grade` in `{0, 1, 2, 3}` derived from latent residual anomaly presence, severity, and employee-cycle context
- **AND** the grade construction is documented in code and in the notebook's label-engineering section

#### Scenario: Ranking formulation can use relevance labels without feature leakage
- **WHEN** employee-pay-cycle ranking formulations are compared
- **THEN** the workflow may use `relevance_grade` as an evaluation or ranking target
- **AND** `y_issue`, `y_dollar`, `relevance_grade`, `rule_missed_severe_issue`, `is_anomaly`, `anomaly_category`, `anomaly_dollars`, and `net_utility` are excluded from active scoring features

### Requirement: Residual payroll ranking rationale
The active employee-pay-cycle notebook SHALL explain why payroll review prioritization benefits from comparing multiple ML formulations on ambiguous residual records rather than assuming one preselected method is correct.

#### Scenario: Formulation rationale is included
- **WHEN** a reviewer reads the feature engineering or model formulations sections of the active employee-pay-cycle notebook
- **THEN** the notebook describes why residual payroll ranking compares classifier, cost-sensitive classifier, regressor, expected-value, and learning-to-rank formulations rather than relying on one unexplained score
- **AND** it explains that the strongest contest is between expected-value reasoning and direct ranking optimization after obvious cases have already been removed by hard rules
