## ADDED Requirements

### Requirement: Latest-period uncertainty-aware analyst review queue
The system SHALL surface risk and uncertainty together in an analyst-safe payroll review queue for the latest pay period only.

#### Scenario: Analyst queue is limited to latest pay period
- **WHEN** analyst review queue generation runs on scored payroll records spanning multiple pay periods
- **THEN** the analyst-safe queue includes only records from the latest available pay period

#### Scenario: Review queue includes risk and uncertainty fields
- **WHEN** analyst review queue generation runs on scored payroll records
- **THEN** each analyst-safe queue row includes final anomaly risk score, uncertainty bucket, composite uncertainty score, primary uncertainty reason, and relevant uncertainty context without exposing injected evaluation labels, injected anomaly dollars, or evaluation-only OOD labels

#### Scenario: Review queue includes pay-period display context
- **WHEN** analyst queue rows are displayed
- **THEN** each row includes a human-readable pay-period date or label in addition to any internal pay-period index

#### Scenario: Review queue includes expected gross-pay interval context
- **WHEN** expected gross-pay interval fields are available
- **THEN** each analyst-safe queue row includes expected gross-pay p10, p50, p90, interval width, and excess over p90 or equivalent analyst-readable interval context

#### Scenario: High-risk medium-uncertainty records remain visible
- **WHEN** a latest-period record has a high risk score and medium uncertainty because a payroll signal such as overtime is highly anomalous but the peer-group sample is small
- **THEN** the review queue surfaces the record with both the high risk score and the medium uncertainty bucket rather than suppressing or hiding the record

#### Scenario: Conformal context is analyst-readable
- **WHEN** conformal percentile is available for a queued record
- **THEN** the review queue or case card explains the percentile in business language such as how unusual the record is relative to recent payroll history

### Requirement: Uncertainty explanations for case cards
The notebooks SHALL show compact case cards that explain both why a payroll record is risky and why its score is uncertain.

#### Scenario: Case card includes risk and uncertainty reasons
- **WHEN** the review queue, explainability, and thresholds notebook displays a selected case card
- **THEN** the case card includes risk category, risk score, uncertainty bucket, why-risky bullets, and why-uncertain bullets using review-safe language

#### Scenario: Uncertainty reasons identify dominant drivers
- **WHEN** uncertainty components are available for a queued record
- **THEN** the explanation identifies dominant uncertainty drivers such as small peer group, limited employee history, model signal disagreement, wide bootstrap interval, wide expected-pay interval, data quality issues, or out-of-distribution context

#### Scenario: Review-safe wording is preserved
- **WHEN** uncertainty-aware explanations are generated
- **THEN** they avoid claiming confirmed misconduct, confirmed fraud, confirmed payroll error, or known synthetic anomaly status
