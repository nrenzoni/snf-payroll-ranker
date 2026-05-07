## ADDED Requirements

### Requirement: Scenario-controlled payroll simulation
The system SHALL support reproducible scenario-controlled synthetic payroll generation using explicit dataclass scenario specifications.

#### Scenario: Default scenario preserves existing generation behavior
- **WHEN** payroll generation runs without a custom scenario specification
- **THEN** the generated payroll dataset includes the existing synthetic payroll fields, anomaly labels, anomaly categories, anomaly dollar impacts, validation compatibility, and reproducible seed behavior

#### Scenario: Scenario specification controls simulation inputs
- **WHEN** payroll generation runs with a scenario specification
- **THEN** the generation process applies the configured anomaly plan, drift plan, and change-point events while retaining required payroll columns and synthetic evaluation labels

#### Scenario: Scenario generation is reproducible
- **WHEN** the same payroll configuration and scenario specification run with the same seed
- **THEN** the generated payroll rows and synthetic label outputs are reproducible across runs

### Requirement: Drift and change-point simulation controls
The system SHALL support controlled drift and change-point events for internal simulation and stress testing.

#### Scenario: Pay-code drift is applied by period
- **WHEN** a scenario specifies pay-code drift beginning at a configured pay period
- **THEN** later payroll periods contain the configured pay-code mix shift without modifying earlier periods outside the event scope

#### Scenario: Payroll amount change point is applied by subgroup
- **WHEN** a scenario specifies a gross-pay, overtime, deduction, or payroll-total shift for a subgroup and period
- **THEN** only matching records in the configured period range and subgroup receive the configured distribution shift

#### Scenario: Scenario metadata identifies applied controls
- **WHEN** scenario-controlled payroll generation completes
- **THEN** pipeline results include scenario metadata identifying which drift, change-point, or anomaly-mix controls were applied

#### Scenario: Scenario metadata is kept out of analyst queue rows
- **WHEN** scenario-controlled outputs are generated
- **THEN** scenario metadata is exposed through internal pipeline results or optional evaluation artifacts rather than analyst-safe queue fields or model feature columns

#### Scenario: Scenario metadata can be persisted for internal review
- **WHEN** pipeline outputs are written for a scenario-controlled run
- **THEN** scenario metadata can be written as a separate internal evaluation artifact without changing source payroll schema or analyst-safe queue schema

### Requirement: Anomaly-mix scenario controls
The system SHALL support configurable synthetic anomaly mix and intensity controls for internal evaluation stress tests.

#### Scenario: Anomaly category mix changes by scenario
- **WHEN** a scenario specifies anomaly category weights or target counts
- **THEN** injected synthetic anomalies follow the configured category mix within reproducible random variation

#### Scenario: Anomaly severity changes by scenario
- **WHEN** a scenario specifies severity multipliers for supported anomaly categories
- **THEN** injected synthetic anomaly dollar impacts and affected payroll fields reflect the configured severity controls

#### Scenario: Payroll-total shift uses subgroup-period multiplier semantics
- **WHEN** a scenario specifies a payroll-total shift for a subgroup and period range
- **THEN** matching records in the configured subgroup and period range receive a configured row-level multiplier or multiplier with bounded noise rather than solving to an exact aggregate total

#### Scenario: Evaluation truth remains separated from scoring features
- **WHEN** scenario-controlled anomalies are injected
- **THEN** injected labels, injected categories, and injected anomaly dollar impacts remain evaluation-only and are not added to model feature columns or analyst-safe queue fields
