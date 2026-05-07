## ADDED Requirements

### Requirement: Diagnostic scenario catalog
The system SHALL provide reusable internal synthetic scenario presets that create distinct diagnostic regimes for data-science review.

#### Scenario: Scenario catalog exposes named regimes
- **WHEN** internal diagnostics request predefined synthetic scenarios
- **THEN** the system provides named scenarios for baseline, rule-friendly anomalies, statistical outliers, ML-friendly rare combinations, exposure-heavy anomalies, subgroup drift, calendar drift, and queue stress

#### Scenario: Scenario presets are reproducible
- **WHEN** the same scenario preset runs with the same payroll configuration and seed
- **THEN** generated payroll rows, injected labels, and scenario metadata are reproducible

#### Scenario: Default generation remains unchanged
- **WHEN** payroll generation runs without a custom scenario or preset
- **THEN** existing default synthetic payroll behavior, schema, reproducibility, and evaluation-only label separation remain available

### Requirement: Targeted anomaly generation controls
The system SHALL support subgroup-period-targeted anomaly propensity, category mix, and severity controls for internal diagnostic scenarios.

#### Scenario: Anomaly propensity targets a subgroup and period range
- **WHEN** a scenario configures anomaly targeting for a subgroup and period range
- **THEN** injected anomaly concentration increases in the configured subgroup-period scope relative to comparable untargeted rows

#### Scenario: Category mix varies by target scope
- **WHEN** a scenario configures category weights for a targeted subgroup-period scope
- **THEN** injected anomaly categories in that scope reflect the configured category mix within reproducible random variation

#### Scenario: Severity distributions vary by target scope
- **WHEN** a scenario configures severity controls for a targeted subgroup-period scope
- **THEN** synthetic anomaly dollar impacts and affected payroll fields reflect the configured severity behavior for matching records

#### Scenario: Targeted controls remain evaluation-only
- **WHEN** targeted scenario controls are applied
- **THEN** scenario metadata, injected labels, injected categories, and injected anomaly dollar impacts remain excluded from model feature columns and analyst-safe queue outputs
