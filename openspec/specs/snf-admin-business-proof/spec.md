## Purpose
Define the facility-administrator business proof for SNF payroll approval value, including repeated-world comparisons, method ladder narrative, proof-first presentation, rolling stability framing, and analyst-ready deliverable expectations.
## Requirements
### Requirement: Repeated-world facility-admin value proof
The business-facing SNF notebook SHALL prove payroll approval value for facility administrators using repeated scenario and seed comparisons rather than a single-world example.

#### Scenario: Main scenarios are aggregated
- **WHEN** the business-facing SNF proof notebook runs
- **THEN** it aggregates calibrated manual threshold pack, deterministic rule, robust statistical, ML-only, and hybrid comparisons across repeated runs of the `baseline`, `overtime-staffing-pressure`, and `premium-mismatch` scenarios using configured facility review budgets

#### Scenario: Evaluation-only truth stays explicit
- **WHEN** proof plots use synthetic labels or synthetic anomaly dollars
- **THEN** the notebook states that those fields are used only for evaluation and do not appear in the final administrator-facing ranked output

### Requirement: Explanation-heavy method ladder narrative
The business-facing SNF notebook SHALL explain what manual thresholds, deterministic rules, robust statistics, ML-only scoring, and hybrid ranking each do, why each method is useful, and where each method is limited for SNF payroll approval.

#### Scenario: Method roles are defined
- **WHEN** a reviewer reads the notebook method ladder section
- **THEN** the notebook describes the practical purpose of thresholds, rules, robust statistics, ML-only scoring, and hybrid ranking in facility-admin payroll review language

#### Scenario: Method limitations are made explicit
- **WHEN** a reviewer reads the notebook narrative around method comparisons
- **THEN** the notebook explains the limitations of single-field thresholds, deterministic-only rules, statistics-only scoring, ML-only scoring, and hybrid ranking so the proof does not overclaim certainty

### Requirement: Proof-first notebook presentation
The business-facing SNF notebook SHALL keep the main narrative focused on business-proof visuals and concise summaries while still showing one concrete final ranked output.

#### Scenario: Main flow limits dense tables
- **WHEN** the notebook presents the main proof narrative
- **THEN** it emphasizes plots and concise summaries and includes at most one concrete final ranked-output table rather than multiple dashboard-style intermediate tables

#### Scenario: Stress diagnostics are appendix-only
- **WHEN** subgroup drift, calendar drift, or queue-stress evidence is presented
- **THEN** it appears in a clearly labeled appendix section after the main business-proof narrative

### Requirement: Realistic rolling stability narrative
The business-facing SNF notebook SHALL present rolling-origin stability as operational review yield over time, not as a promise of perfect precision.

#### Scenario: Rolling-origin stability remains credible
- **WHEN** the notebook shows rolling-origin evidence
- **THEN** the headline plot uses facility-period yield or value-capture metrics and the surrounding narrative states that synthetic labels are evaluation-only and that real SNF payroll review will include legitimate high-risk-looking records

### Requirement: Analyst-ready proof presentation
The business-facing SNF notebook SHALL present proof visuals and takeaways in a form suitable for a facility-admin deliverable rather than as exploratory analysis output.

#### Scenario: Main proof avoids dashboard artifacts
- **WHEN** the notebook renders the main proof flow
- **THEN** it avoids raw intermediate DataFrame outputs and keeps only one concrete administrator-facing ranked-output table

#### Scenario: Main proof visuals are scenario-clear
- **WHEN** repeated-world or manual-threshold evidence spans multiple scenario families
- **THEN** each plot or adjacent takeaway makes the scenario scope explicit so readers can distinguish pooled proof from scenario-specific proof

#### Scenario: Proof visuals include operational takeaways
- **WHEN** a major proof visual is shown
- **THEN** the notebook includes a concise quantified takeaway or interpretation that explains the operational implication for facility payroll approval
