## MODIFIED Requirements

### Requirement: Leakage-safe feature engineering
The system SHALL compute employee-pay-cycle features using only information available before the scored payroll cycle and SHALL treat employee-pay-cycle records as the active feature-engineering contract.

#### Scenario: Rolling history excludes current and future periods
- **WHEN** rolling employee or facility features such as pay medians, gross-pay standard deviation, overtime baseline, or payroll-cycle history are computed
- **THEN** the calculation excludes the current payroll cycle and all future cycles

#### Scenario: Temporal split avoids random row leakage
- **WHEN** model training and scoring datasets are prepared
- **THEN** active employee-pay-cycle records are split by payroll cycle rather than random employee-cycle rows

### Requirement: Machine learning anomaly scoring
The system SHALL support supervised and ranking-oriented employee-pay-cycle scoring interfaces suitable for Phase 1 production-oriented research rather than requiring a single active unsupervised anomaly model.

#### Scenario: Multiple formulation interfaces are supported
- **WHEN** active model training or scoring is implemented
- **THEN** the runtime contract supports employee-pay-cycle classification, regression, expected-value, or learning-to-rank formulations as comparable active scoring paths

#### Scenario: Active scoring interfaces stay label-safe
- **WHEN** synthetic or adjudicated labels are present for research evaluation
- **THEN** active scoring features exclude evaluation-only truth fields and use only approved feature contracts for training, calibration, or scoring

## ADDED Requirements

### Requirement: Phase-gated production promotion
The scoring library SHALL treat Phase 1 formulation comparison as a gate for later production promotion rather than declaring any single method as the active production answer in advance.

#### Scenario: Production candidacy is evidence-based
- **WHEN** an active scoring method is proposed for later operational use
- **THEN** the project documents that promotion depends on evaluation, generalization, uncertainty, and explainability evidence from the active research phase

## REMOVED Requirements

### Requirement: Configurable hybrid ranking score
**Reason**: The hybrid shift-level score is no longer the active project contract and should not remain normative while the employee-pay-cycle runtime direction is being rebuilt.
**Migration**: Retain the old hybrid logic only as deprecated historical reference and move active scoring requirements to employee-pay-cycle formulation interfaces.
