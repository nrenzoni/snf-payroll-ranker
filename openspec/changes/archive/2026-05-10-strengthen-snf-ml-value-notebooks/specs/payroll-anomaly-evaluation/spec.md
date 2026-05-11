## ADDED Requirements

### Requirement: Technical ML value and ablation notebook
The notebook sequence SHALL include a technical validation notebook that demonstrates incremental ML and hybrid ranking value using evaluation-safe synthetic labels and temporal validation framing.

#### Scenario: Ablation notebook compares method ladder
- **WHEN** the technical ML value notebook runs
- **THEN** it compares manual threshold baselines, deterministic rule score, robust statistical score, ML score, and hybrid score using approval-budget metrics, PR-AUC, rank metrics, exposure capture, and dollar capture where available

#### Scenario: Ablation notebook explains complexity value
- **WHEN** a reviewer reads the technical ML value notebook
- **THEN** narrative text explains what each method level adds, where complexity improves review prioritization, and where simpler components remain useful

### Requirement: Incremental value plots
The evaluation notebook sequence SHALL include plot-ready evidence that makes incremental method value observable.

#### Scenario: Method-complexity visuals render
- **WHEN** the technical ML value notebook runs
- **THEN** it renders visuals or tables such as an incremental complexity waterfall, component comparison heatmap, precision or exposure by review budget, and threshold-miss or false-positive summaries

#### Scenario: Temporal and uncertainty context remain visible
- **WHEN** the technical ML value notebook reports ablation or model comparison results
- **THEN** it includes temporal validation context and uncertainty, stability, or risk-coverage diagnostics where existing pipeline outputs support them
