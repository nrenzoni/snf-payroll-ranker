## ADDED Requirements

### Requirement: Feature engineering notebook walkthrough
The notebooks SHALL demonstrate historical employee features, peer-relative features, deterministic rule-based flags, and robust statistical features using concrete synthetic payroll records.

#### Scenario: Concrete feature examples are displayed
- **WHEN** the feature engineering and baselines notebook runs
- **THEN** it displays selected records with current gross pay, prior rolling median, percentage change, peer median, peer deviation, rule reason codes, and component scores

### Requirement: Leakage-safe feature explanation
The notebooks SHALL explain which features are leakage-safe and why injected labels are retained for evaluation but not used as training or scoring features.

#### Scenario: Leakage-safe narrative is present
- **WHEN** a reviewer reads the feature engineering and baselines notebook
- **THEN** the notebook states that historical features exclude current and future periods and that labels are not used as model features

### Requirement: Baseline scoring comparison inputs
The notebooks SHALL demonstrate rule score, statistical score, ML score, and hybrid score as separate baseline ranking signals using the existing model comparison output.

#### Scenario: Baseline score columns are compared
- **WHEN** the feature engineering and modeling notebooks run
- **THEN** they display rule, statistical, ML, and hybrid score columns and explain what each contributes to payroll review prioritization

### Requirement: Payroll hybrid ranking rationale
The notebooks SHALL explain why a hybrid ranking is appropriate for payroll because deterministic compliance issues, statistical outliers, peer context, employee history, and dollar impact capture different review risks.

#### Scenario: Hybrid rationale is included
- **WHEN** a reviewer reads the feature engineering or modeling notebook
- **THEN** the notebook describes why payroll ranking combines rule-based, statistical, ML, peer/history, and dollar-impact signals rather than relying on a single model score
