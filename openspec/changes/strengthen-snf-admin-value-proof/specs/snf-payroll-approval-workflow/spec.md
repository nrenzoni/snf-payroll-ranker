## MODIFIED Requirements

### Requirement: Manual threshold value comparison
The system SHALL compare automated SNF anomaly ranking against administrator-style threshold baselines that include individual threshold signals and a calibrated combined manual threshold baseline.

#### Scenario: Threshold baselines are generated
- **WHEN** evaluation runs on synthetic SNF payroll data
- **THEN** results include baseline performance for the calibrated manual threshold pack, gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled variance, and facility payroll variance thresholds

#### Scenario: Automated ranking value is summarized
- **WHEN** threshold and automated ranking results are available
- **THEN** notebooks summarize review volume, native review burden, estimated exposure captured, estimated exposure captured per reviewed record, false positives avoided, and missed high-exposure exceptions for each approach, with the calibrated manual threshold pack serving as the primary manual comparator

### Requirement: Business-facing SNF ML value proof
The SNF case-study notebook SHALL demonstrate the operational value of automated hybrid approval ranking for facility administrators using repeated scenario evidence and explanation-rich comparison against manual threshold review.

#### Scenario: Business proof compares repeated scenario worlds
- **WHEN** the SNF case-study notebook runs
- **THEN** it compares the calibrated manual threshold pack, deterministic rules, robust statistics, ML-only scoring, and hybrid ranking across repeated scenario and seed worlds for `baseline`, `overtime-staffing-pressure`, and `premium-mismatch` using configured facility review budgets

#### Scenario: Business narrative explains operational value
- **WHEN** a reviewer reads the SNF case-study notebook
- **THEN** narrative text explains what each method type does, where it helps facility approval review, and where thresholds, rules, statistics, ML-only scoring, and hybrid ranking each remain limited

#### Scenario: Business-safe concrete output remains visible
- **WHEN** the main proof narrative concludes
- **THEN** the notebook shows one concrete final ranked-output table with review-safe queue fields so facility administrators can see what the deployed output looks like without relying on multiple intermediate dashboard tables

## ADDED Requirements

### Requirement: Appendix stress diagnostics
The SNF case-study notebook SHALL separate stress evidence from the primary business proof.

#### Scenario: Stress variants are shown in appendix
- **WHEN** subgroup drift, calendar drift, or queue stress evidence is presented
- **THEN** it appears in a clearly labeled appendix section after the main proof narrative

#### Scenario: Appendix stress evidence avoids alias overclaim
- **WHEN** stress appendix comparisons are generated
- **THEN** the notebook uses true stress diagnostics or clearly labeled stress constructions rather than presenting simple scenario aliases as distinct stress worlds
