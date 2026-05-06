## ADDED Requirements

### Requirement: Notebook demonstrates each requested modeling mistake
The notebook SHALL include demonstrations for random train/test splitting, default-only Isolation Forest usage, ROC-AUC-only reporting, false-positive neglect, equal anomaly prioritization, and overclaiming fraud detection.

#### Scenario: Reader reviews mistake coverage
- **WHEN** the modeling and evaluation notebook is opened
- **THEN** each requested mistake is present as a distinct explained demonstration

### Requirement: Each demonstration compares anti-pattern and corrected method
Each mistake demonstration SHALL show an explicit anti-pattern example and compare it against a corrected method using the existing payroll anomaly ranking context.

#### Scenario: Reader compares methods
- **WHEN** a mistake demonstration is executed
- **THEN** the anti-pattern output and corrected-method output are both visible and labeled so the difference is clear

### Requirement: Demonstrations include plots
Each mistake demonstration SHALL include at least one Lets-plot visualization or plotted comparison that makes the problem observable.

#### Scenario: Reader inspects visual evidence
- **WHEN** a demonstration section is run
- **THEN** the notebook renders a plot that supports the explanation of why the anti-pattern is problematic

### Requirement: Evaluation demonstrations use operational metrics
The notebook SHALL compare generic model metrics with payroll review metrics such as Precision@K, PR-AUC, false positives, false negatives, dollar capture, review budget effects, or rank-based outcomes where relevant.

#### Scenario: Reader evaluates ranking quality
- **WHEN** the notebook compares ROC-AUC-only reporting against corrected evaluation
- **THEN** the corrected evaluation includes review-budget or imbalance-aware metrics beyond ROC-AUC

### Requirement: Anomaly importance is cost-aware
The notebook SHALL demonstrate that anomalies differ by business impact and that prioritization must consider severity, dollar exposure, category, or review capacity instead of treating all anomaly labels as equal.

#### Scenario: Reader evaluates anomaly prioritization
- **WHEN** the equal-importance anti-pattern is shown
- **THEN** the corrected comparison ranks or summarizes anomalies using impact-aware information

### Requirement: Fraud-detection claims are constrained
The notebook SHALL explicitly distinguish synthetic anomaly detection and review prioritization from confirmed fraud detection.

#### Scenario: Reader reaches conclusion section
- **WHEN** the notebook summarizes what the demos prove
- **THEN** it states that the workflow surfaces review candidates and synthetic exceptions, not confirmed fraud
