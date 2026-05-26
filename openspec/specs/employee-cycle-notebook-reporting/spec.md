## Purpose
Define the single active employee-pay-cycle notebook contract for residual payroll review reporting.

## Requirements
### Requirement: Single active employee-pay-cycle notebook
The repository SHALL provide one primary Jupytext percent-format notebook under `notebooks/` as the active reporting deliverable for the employee-pay-cycle program.

#### Scenario: Active notebook exists
- **WHEN** the active notebook deliverable is reviewed
- **THEN** the repository includes one primary Jupytext percent-format notebook under `notebooks/` for the employee-pay-cycle workflow
- **AND** legacy notebook sequences are identified as historical reference rather than active contract requirements

### Requirement: Fixed notebook section mapping
The primary employee-pay-cycle notebook SHALL preserve the fixed section mapping used by the active reporting contract.

#### Scenario: Main narrative section order is preserved
- **WHEN** a reviewer reads the active notebook from top to bottom
- **THEN** the notebook sections appear in this order: `0. Executive Summary`, `1. Problem Framing: Residual Payroll Review After Hard Rules`, `2. Synthetic SNF Payroll Data Generation`, `3. Hard Rule Gate: Defining the Residual Universe`, `4. Simulation Sanity Checks for the Residual Dataset`, `5. Label Engineering for Residual Ranking`, `6. Feature Engineering for Ambiguous Payroll Records`, `7. Model Formulations`, `8. Main Results: Residual Queue Evaluation`, `9. Ablation Studies`, `10. Diagnostics, Explanations, and Final Recommendation`, and `11. Technical Appendix`

### Requirement: Technical appendix coverage
The primary employee-pay-cycle notebook SHALL include a clearly labeled technical appendix after the main narrative.

#### Scenario: Appendix covers required deep-dive topics
- **WHEN** the technical appendix is reviewed
- **THEN** it includes data dictionary, hard rule definitions, metric definitions, ranking group construction, handling zero-positive residual groups, hyperparameter search space, additional ablation tables, additional calibration plots, and stress-test configurations

### Requirement: Active notebook uses employee-pay-cycle evidence
The primary employee-pay-cycle notebook SHALL base its narrative, tables, and plots on active employee-pay-cycle runtime artifacts rather than deprecated shift-level notebook contracts.

#### Scenario: Active notebook aligns with employee-pay-cycle runtime
- **WHEN** a section presents data generation, scoring, evaluation, queue, or production-candidacy evidence
- **THEN** the evidence is sourced from employee-pay-cycle pipeline outputs or notebook-owned assembly built from those active outputs
- **AND** deprecated shift-level notebook paths are not treated as the active source of proof

### Requirement: Notebook frames stage-2 residual review explicitly
The primary employee-pay-cycle notebook SHALL define hard rules as an upstream gate and treat residual ML ranking as the main question under study.

#### Scenario: Residual-review framing is explicit
- **WHEN** a reviewer reads the executive summary, problem framing, or hard-rule gate sections
- **THEN** the notebook states that hard rules remove obvious payroll problems before ML comparison begins
- **AND** it states that the notebook does not ask whether ML beats hard rules on obvious problems, but whether ML adds value after those obvious cases have already been removed
- **AND** it states that compliance, PBJ, and HPRD are out of scope for targets, features, and evaluation metrics

### Requirement: Notebook review-budget framing is percent-based
The primary employee-pay-cycle notebook SHALL frame active review-budget analysis as the percentage of each facility-pay-period residual queue reviewed rather than as an absolute count of records reviewed.

#### Scenario: Percent-budget framing is explicit in notebook results
- **WHEN** a reviewer reads the active notebook's evaluation, workflow, or visualization sections
- **THEN** the notebook defines review budget as the configured share of each facility-pay-period residual queue reviewed
- **AND** it explains any rounding or minimum-reviewed-record rule used to convert percentages into grouped reviewed counts
- **AND** axes, tables, and narrative refer to review-budget percentages rather than absolute K values for the active residual-ranking study

### Requirement: Label-engineering section is implementation-backed
The notebook's label-engineering section SHALL describe the real employee-pay-cycle label formulas used by the active runtime rather than placeholder concepts.

#### Scenario: Label section explains residual labels
- **WHEN** a reviewer reads section `5. Label Engineering for Residual Ranking`
- **THEN** it explains how employee-pay-cycle residual `y_issue`, residual `y_dollar`, dominant `anomaly_category`, `relevance_grade`, `rule_missed_severe_issue`, `observed_correction`, and `net_utility` are constructed
- **AND** it states which labels are evaluation-only and excluded from scoring inputs
