## MODIFIED Requirements

### Requirement: Fixed notebook section mapping
The primary employee-pay-cycle notebook SHALL preserve a fixed decision-oriented section mapping used by the active reporting contract.

#### Scenario: Main narrative section order is preserved
- **WHEN** a reviewer reads the active notebook from top to bottom
- **THEN** the notebook sections appear in this order: `0. Executive Summary`, `1. Problem Framing: Residual Payroll Review After Hard Rules`, `2. Synthetic DGP Design and Scenario Suite`, `3. Hard Rule Gate: Defining the Residual Universe`, `4. Residual Benchmark Stress Design`, `5. Label Engineering for Residual Ranking`, `6. Feature Engineering for Ambiguous Payroll Records`, `7. Model Formulations`, `8. Main Study: DGP Scenario-Based Residual Ranking Benchmark`, `9. Ablation Studies`, `10. Diagnostics, Explanations, and Final Recommendation`, and `11. Technical Appendix`
- **AND** section `4. Residual Benchmark Stress Design` may be implemented as a short bridge section or merged into the surrounding synthetic DGP and label-engineering narrative when the technical appendix retains the detailed simulation sanity evidence

### Requirement: Notebook demonstrates residual-risk heterogeneity
The primary employee-pay-cycle notebook SHALL show compact evidence that the residual ranking task contains meaningful heterogeneity before asking reviewers to interpret formulation-comparison plots, while keeping detailed sanity-check tables out of the main narrative unless they directly support the decision story.

#### Scenario: Residual-task heterogeneity evidence is visible
- **WHEN** a reviewer reads the active notebook's residual benchmark stress-design, label-engineering, or model-formulation sections
- **THEN** the notebook shows concise diagnostics describing residual anomaly-family mix, severe-label selectivity, and relevance-grade distribution
- **AND** the notebook explains why those diagnostics matter for interpreting classifier, regressor, expected-value, and learning-to-rank comparisons

#### Scenario: Model similarity evidence accompanies comparison visuals
- **WHEN** the active notebook presents model-comparison visuals or summaries for the residual queue
- **THEN** it also shows whether candidate models are producing materially different rankings through score-correlation, top-budget overlap, or equivalent similarity diagnostics
- **AND** it does not present near-flat comparison plots without enough surrounding context to explain whether the underlying residual task is genuinely differentiating the candidate formulations

#### Scenario: Scenario-aware sanity checks are summarized in the main narrative
- **WHEN** a reviewer reads the main narrative before the appendix
- **THEN** the notebook summarizes that DGP scenarios vary residual issue rate, severe issue rate, residual dollars, dominant issue family, and label-bias strength
- **AND** the main narrative uses concise prose, plot-first evidence, or a compact card as the primary reader-facing scenario sanity summary rather than requiring a broad raw dataframe table
- **AND** detailed cross-scenario sanity tables are available in the technical appendix or another clearly labeled audit-support location

#### Scenario: Main benchmark is described as holdout evidence
- **WHEN** a reviewer reads the main scenario-based benchmark section
- **THEN** the notebook describes those benchmark summaries as temporally held-out scenario-seed evidence rather than same-sample model-fit results

### Requirement: Scenario-based executive summary and main study framing
The active employee-pay-cycle notebook SHALL present its executive summary and section 8 conclusions as aggregated DGP scenario-based benchmark findings rather than single-run main results, using plot-first or card-first reader-facing summaries in the main narrative and detailed tables as appendix support.

#### Scenario: Executive summary uses aggregated framing
- **WHEN** a reviewer reads section `0. Executive Summary`
- **THEN** the notebook describes the main study as evaluating models across multiple synthetic SNF payroll data-generating processes and seeds
- **AND** the notebook's winner language is based on scenario-seed aggregation rather than phrasing such as "in this run"

#### Scenario: Main study outputs are scenario-based and decision-focused
- **WHEN** a reviewer reads section `8. Main Study: DGP Scenario-Based Residual Ranking Benchmark`
- **THEN** the section presents aggregate winner frequency, metric interval evidence, and a winner map by operating objective and review-budget percentage using plots, compact tables, or decision cards suitable for reader-facing interpretation
- **AND** detailed DGP scenario catalog rows, scenario-seed study design rows, raw aggregate winner-frequency rows, and full median metric tables are available in the technical appendix or another clearly labeled audit-support location

### Requirement: Section 2 describes the scenario family
The active employee-pay-cycle notebook SHALL describe the synthetic payroll world as a family of DGP scenarios rather than as only one simulated world.

#### Scenario: Scenario suite appears after the DGP diagram
- **WHEN** a reviewer reads section `2. Synthetic DGP Design and Scenario Suite`
- **THEN** the notebook retains the synthetic-world diagram
- **AND** it follows the diagram with a concise scenario-suite summary describing the implemented DGP suite and what changes in each scenario
- **AND** it explains that the scenario suite varies the synthetic data-generating process rather than the model objective or review capacity
- **AND** detailed scenario catalog rows may be placed in the technical appendix when the main narrative uses a shorter scenario-suite summary
