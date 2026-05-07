## ADDED Requirements

### Requirement: Plot-calibrated internal diagnostic scenarios
The system SHALL calibrate internal diagnostic scenario presets so rendered internal notebooks receive visibly contrasting synthetic conditions while default generation remains unchanged.

#### Scenario: Scenario presets produce observable contrast
- **WHEN** internal diagnostic scenario presets are generated with bounded notebook defaults
- **THEN** at least the rule-friendly, statistical-friendly, exposure-heavy, subgroup-drift, calendar-drift, and queue-stress presets produce measurable differences in category mix, anomaly dollars, subgroup-period concentration, score quantiles, or threshold candidate demand relative to baseline

#### Scenario: Rule-friendly scenario creates rule-visible anomalies
- **WHEN** the rule-friendly scenario is generated
- **THEN** the generated anomalies include enough deterministic-rule-visible cases such as missing deductions, negative net pay, pay after termination, or duplicate payments to create non-flat rule-signal diagnostic outputs

#### Scenario: Queue-stress scenario creates candidate demand
- **WHEN** the queue-stress scenario is scored under bounded internal notebook settings
- **THEN** it produces enough high-scoring candidate records for threshold-demand queue plots to show demand and overload variation rather than empty queues

#### Scenario: Default generation remains stable
- **WHEN** payroll generation runs without an internal diagnostic scenario
- **THEN** default schema, reproducibility, anomaly label separation, and analyst-safe leakage boundaries remain unchanged

### Requirement: Scenario contrast summaries
The system SHALL provide scenario summary data suitable for diagnosing whether internal plots will be dense enough to interpret.

#### Scenario: Scenario summary includes score and demand context
- **WHEN** scenario summaries are generated for internal diagnostics
- **THEN** the output includes scenario identifier, row count, anomaly count, anomaly rate, anomaly dollars, score quantiles, candidate counts at configured thresholds or quantiles, category mix, and subgroup-period concentration fields

#### Scenario: Sparse scenario conditions are visible
- **WHEN** a configured scenario produces no candidates above an operational threshold or has insufficient subgroup concentration
- **THEN** the summary output makes that sparse condition visible before chart rendering
