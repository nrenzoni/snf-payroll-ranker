## MODIFIED Requirements

### Requirement: Business deliverable notebook sections
The active notebook SHALL include business, technical, evaluation, reviewer-workflow, and production-readiness sections needed for a presentable employee-pay-cycle payroll ranking deliverable.

#### Scenario: Notebook narrative is complete
- **WHEN** a reviewer reads the active notebook
- **THEN** it includes an executive summary, privacy disclaimer, employee-pay-cycle problem framing, anomaly taxonomy, synthetic data generation, schema and data quality summaries, label engineering, feature engineering, model formulations, main queue-based evaluation, generalization evidence, ablation studies, deep diagnostics, reviewer UX, robustness or stress testing, production recommendation, and technical appendix material

### Requirement: Multi-notebook business case study sequence
The repository SHALL treat one primary employee-pay-cycle notebook as the active reporting deliverable instead of a required multi-notebook sequence.

#### Scenario: Active notebook replaces required sequence
- **WHEN** the active reporting contract is implemented
- **THEN** the repository includes one primary Jupytext percent-format employee-pay-cycle notebook under `notebooks/`
- **AND** legacy notebook sequences are not treated as required active deliverables

### Requirement: Executive takeaway and proof summary sections
The active notebook SHALL begin with a short executive takeaway and end its main narrative with a concise production recommendation before the technical appendix.

#### Scenario: Active notebook has business framing
- **WHEN** a reviewer opens the active notebook
- **THEN** the first section contains an executive takeaway
- **AND** the final main-narrative section provides the production recommendation before the appendix begins

### Requirement: Required business visuals
The active notebook SHALL include clean visuals or tables for employee-pay-cycle payroll summaries, score distributions, threshold or formulation comparisons, precision@K by review budget, exposure captured@K by review budget, model comparison, backtest or rolling-origin metrics over time, and selected reviewer-facing queue examples.

#### Scenario: Required visuals render from synthetic employee-pay-cycle outputs
- **WHEN** the active notebook is run on a clean checkout
- **THEN** the required visuals or tables render using synthetic employee-pay-cycle data and generated evaluation outputs
- **AND** notebook cells that render Lets-Plot visuals call `LetsPlot.setup_html()` before displaying those charts
- **AND** continuous distribution visuals use binned histograms or equivalent aggregation rather than one bar per raw numeric value

### Requirement: README notebook sequence documentation
The README SHALL identify the single active employee-pay-cycle notebook and briefly explain that it covers the full reporting story and appendix.

#### Scenario: README links active notebook story
- **WHEN** a reviewer reads `README.md`
- **THEN** it identifies the single active employee-pay-cycle notebook as the active reporting contract
- **AND** it explains that the notebook covers the main payroll anomaly ranking case study and technical appendix in one deliverable
