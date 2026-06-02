## MODIFIED Requirements

### Requirement: Fixed notebook section mapping
The primary employee-pay-cycle notebook SHALL preserve the fixed section mapping used by the active reporting contract.

#### Scenario: Main narrative section order is preserved
- **WHEN** a reviewer reads the active notebook from top to bottom
- **THEN** the notebook sections appear in this order: `0. Executive Summary`, `1. Problem Framing: Residual Payroll Review After Hard Rules`, `2. Synthetic DGP Design and Scenario Suite`, `3. Hard Rule Gate: Defining the Residual Universe`, `4. Simulation Sanity Checks for the Residual Dataset`, `5. Label Engineering for Residual Ranking`, `6. Feature Engineering for Ambiguous Payroll Records`, `7. Model Formulations`, `8. Main Study: DGP Scenario-Based Residual Ranking Benchmark`, `9. Ablation Studies`, `10. Diagnostics, Explanations, and Final Recommendation`, and `11. Technical Appendix`

### Requirement: Active notebook uses employee-pay-cycle evidence
The primary employee-pay-cycle notebook SHALL base its narrative, tables, and plots on active employee-pay-cycle runtime artifacts rather than deprecated shift-level notebook contracts.

#### Scenario: Active notebook aligns with employee-pay-cycle runtime
- **WHEN** a section presents data generation, scoring, evaluation, queue, or production-candidacy evidence
- **THEN** the evidence is sourced from employee-pay-cycle pipeline outputs or notebook-owned assembly built from those active outputs
- **AND** deprecated shift-level notebook paths are not treated as the active source of proof
- **AND** the notebook's main benchmark evidence is assembled from scenario-seed employee-cycle runtime outputs rather than a single baseline-only run

### Requirement: Notebook demonstrates residual-risk heterogeneity
The primary employee-pay-cycle notebook SHALL show compact evidence that the residual ranking task contains meaningful heterogeneity before asking reviewers to interpret formulation-comparison plots.

#### Scenario: Residual-task heterogeneity evidence is visible
- **WHEN** a reviewer reads the active notebook's residual sanity-check, label-engineering, or model-formulation sections
- **THEN** the notebook shows concise diagnostics describing residual anomaly-family mix, severe-label selectivity, and relevance-grade distribution
- **AND** the notebook explains why those diagnostics matter for interpreting classifier, regressor, expected-value, and learning-to-rank comparisons

#### Scenario: Model similarity evidence accompanies comparison visuals
- **WHEN** the active notebook presents model-comparison visuals or summaries for the residual queue
- **THEN** it also shows whether candidate models are producing materially different rankings through score-correlation, top-budget overlap, or equivalent similarity diagnostics
- **AND** it does not present near-flat comparison plots without enough surrounding context to explain whether the underlying residual task is genuinely differentiating the candidate formulations

#### Scenario: Scenario-aware sanity checks are shown
- **WHEN** a reviewer reads section `4. Simulation Sanity Checks for the Residual Dataset`
- **THEN** the notebook includes a compact cross-scenario summary table covering residual issue rate, severe issue rate, residual dollars, dominant issue family, and label-bias strength
- **AND** any retained detailed sanity plots are explicitly framed as baseline illustrative examples rather than the main experimental evidence

## ADDED Requirements

### Requirement: Scenario-based executive summary and main study framing
The active employee-pay-cycle notebook SHALL present its executive summary and section 8 conclusions as aggregated DGP scenario-based benchmark findings rather than single-run main results.

#### Scenario: Executive summary uses aggregated framing
- **WHEN** a reviewer reads section `0. Executive Summary`
- **THEN** the notebook describes the main study as evaluating models across multiple synthetic SNF payroll data-generating processes and seeds
- **AND** the notebook's winner language is based on scenario-seed aggregation rather than phrasing such as "in this run"

#### Scenario: Main study outputs are scenario-based
- **WHEN** a reviewer reads section `8. Main Study: DGP Scenario-Based Residual Ranking Benchmark`
- **THEN** the section shows the DGP scenario catalog, the scenario-seed study design, aggregate winner frequency, a median metric table with intervals, and a winner map by operating objective and review-budget percentage

### Requirement: Section 2 describes the scenario family
The active employee-pay-cycle notebook SHALL describe the synthetic payroll world as a family of DGP scenarios rather than as only one simulated world.

#### Scenario: Scenario suite table appears after the DGP diagram
- **WHEN** a reviewer reads section `2. Synthetic DGP Design and Scenario Suite`
- **THEN** the notebook retains the synthetic-world diagram
- **AND** it follows the diagram with a scenario table describing the implemented DGP suite and what changes in each scenario
- **AND** it explains that the scenario suite varies the synthetic data-generating process rather than the model objective or review capacity
