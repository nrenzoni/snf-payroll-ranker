## ADDED Requirements

### Requirement: Uncertainty quality evaluation
The system SHALL evaluate whether uncertainty scores provide useful context for synthetic payroll anomaly ranking using evaluation-labeled historical records.

#### Scenario: Precision is reported by uncertainty bucket
- **WHEN** evaluation-labeled scored records include uncertainty buckets
- **THEN** the evaluation output reports precision or anomaly rate by Low, Medium, and High uncertainty buckets

#### Scenario: Risk-coverage curve is reported
- **WHEN** evaluation-labeled scored records include uncertainty scores
- **THEN** the evaluation output reports risk-coverage results showing model performance as increasingly uncertain records are excluded or included

#### Scenario: Abstention impact is reported
- **WHEN** an uncertainty threshold or top uncertain fraction is applied for analysis
- **THEN** the evaluation output reports how precision or review quality changes when high-uncertainty records are abstained from automated prioritization analysis

#### Scenario: Existing review-budget metrics remain available
- **WHEN** uncertainty evaluation is generated
- **THEN** existing precision@K, recall@K, dollars captured@K, model comparison, and category error analysis outputs remain available across historical evaluation periods

### Requirement: Expected-pay interval evaluation
The system SHALL evaluate expected gross-pay interval behavior in evaluation-labeled synthetic outputs.

#### Scenario: Interval coverage is reported for normal records
- **WHEN** expected gross-pay interval fields and evaluation labels are available
- **THEN** the evaluation output reports how often non-anomalous records fall within the expected p10 to p90 interval

#### Scenario: Anomaly exceedance is reported
- **WHEN** expected gross-pay p90 and evaluation labels are available
- **THEN** the evaluation output reports how often synthetic anomalies exceed expected p90 and summarizes excess over p90

#### Scenario: Interval width is summarized
- **WHEN** expected gross-pay interval fields are available
- **THEN** the evaluation output summarizes interval width overall and by uncertainty bucket

### Requirement: Latest queue and historical metrics separation
The system SHALL keep operational latest-period queue behavior separate from historical evaluation metrics.

#### Scenario: Analyst queue is latest-period while metrics remain historical
- **WHEN** pipeline outputs include an analyst-safe review queue and evaluation metrics
- **THEN** the analyst-safe queue contains latest-period records only and evaluation metrics continue to summarize historical scored periods where appropriate

### Requirement: Uncertainty evaluation notebook coverage
The notebooks SHALL explain how uncertainty diagnostics fit into the payroll anomaly review workflow.

#### Scenario: Modeling and evaluation notebook shows uncertainty diagnostics
- **WHEN** the modeling, evaluation, and error analysis notebook runs
- **THEN** it displays uncertainty component summaries, expected gross-pay interval diagnostics, precision by uncertainty bucket, and a risk-coverage table or chart

#### Scenario: Production monitoring notebook documents uncertainty limits
- **WHEN** the production monitoring and deployment path notebook is reviewed
- **THEN** it documents uncertainty monitoring, calibration uncertainty as dependent on future analyst feedback labels, OOD monitoring for pay-code drift, and limitations of synthetic-label uncertainty evaluation
