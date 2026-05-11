## ADDED Requirements

### Requirement: Narrative case-study approval evidence
The review queue notebooks SHALL include narrative interpretation around business-facing case-study plots and tables so administrator reviewers can understand what each output proves.

#### Scenario: Narrative accompanies case-study outputs
- **WHEN** the SNF case-study notebook displays lift scorecards, threshold comparisons, case cards, facility summaries, or scenario plots
- **THEN** nearby markdown explains how to read the output, what operational decision it supports, and why the wording remains review-safe

### Requirement: Business-facing case-study visuals
The SNF case-study notebook SHALL include administrator-oriented visuals or tables that make the approval value of the ranked queue clear.

#### Scenario: Approval value visuals render
- **WHEN** the SNF case-study notebook runs
- **THEN** it renders visuals or tables for exposure captured per reviewed record, false-positive avoidance, missed high-risk records, facility approval concentration, and selected administrator-safe case cards where source data is available

#### Scenario: Case-study visuals exclude evaluation truth
- **WHEN** business-facing case-study visuals or case cards are displayed
- **THEN** they exclude injected anomaly labels, injected anomaly categories, and injected anomaly dollar impacts unless the section is explicitly labeled as evaluation-only
