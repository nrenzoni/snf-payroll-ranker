## ADDED Requirements

### Requirement: Score component contribution narrative
The notebooks SHALL explain the contribution of each major scoring component to SNF payroll approval prioritization.

#### Scenario: Component contributions are displayed
- **WHEN** the SNF case-study or technical ML value notebook runs
- **THEN** it displays rule, statistical, schedule/timeclock, premium eligibility, ML, exposure, and hybrid score context where available for selected ranked records or aggregate method comparisons

#### Scenario: Hybrid rationale is tied to evidence
- **WHEN** the notebooks compare component scores with hybrid ranking
- **THEN** they explain why payroll approval benefits from combining deterministic rules, robust statistics, ML multivariate unusualness, schedule/timeclock context, premium eligibility, and estimated exposure rather than relying on one signal alone

### Requirement: ML-only value is separated from hybrid value
The technical ML value notebook SHALL distinguish the value of the ML score alone from the value of the full hybrid ranking.

#### Scenario: ML and hybrid are compared separately
- **WHEN** method-comparison outputs are displayed
- **THEN** ML-only metrics and hybrid-ranking metrics appear as separate methods so reviewers can see whether the hybrid score improves beyond unsupervised ML alone
