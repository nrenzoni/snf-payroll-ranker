## ADDED Requirements

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
- **THEN** the notebook sections appear in this order: `0. Executive Summary`, `1. Problem Framing`, `2. Data-Generating Process`, `3. Simulation Sanity Checks`, `4. Label Engineering`, `5. Feature Engineering`, `6. Model Formulations`, `7. Main Queue-Based Results`, `8. Generalization Results`, `9. Ablation Studies`, `10. Deep Diagnostics`, `11. Model Explanation and Reviewer UX`, `12. Robustness / Stress Tests`, `13. Final Production Recommendation`, and `14. Technical Appendix`

### Requirement: Technical appendix coverage
The primary employee-pay-cycle notebook SHALL include a clearly labeled technical appendix after the main narrative.

#### Scenario: Appendix covers required deep-dive topics
- **WHEN** the technical appendix is reviewed
- **THEN** it includes metric implementation details, full ablation matrix, hyperparameter search details, extra calibration plots, full stress-test grid, feature importance by split, per-facility diagnostics, label-bias simulation variants, and mathematical ranking objective notes

### Requirement: Active notebook uses employee-pay-cycle evidence
The primary employee-pay-cycle notebook SHALL base its narrative, tables, and plots on active employee-pay-cycle runtime artifacts rather than deprecated shift-level notebook contracts.

#### Scenario: Active notebook aligns with employee-pay-cycle runtime
- **WHEN** a section presents data generation, scoring, evaluation, queue, or production-candidacy evidence
- **THEN** the evidence is sourced from employee-pay-cycle pipeline outputs or notebook-owned assembly built from those active outputs
- **AND** deprecated shift-level notebook paths are not treated as the active source of proof
