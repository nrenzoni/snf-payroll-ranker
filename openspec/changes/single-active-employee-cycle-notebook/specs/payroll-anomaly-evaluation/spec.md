## MODIFIED Requirements

### Requirement: Technical ML value and ablation notebook
The active employee-pay-cycle notebook SHALL include sections that demonstrate incremental formulation value using evaluation-safe synthetic labels and temporal validation framing.

#### Scenario: Ablation section compares method ladder
- **WHEN** the active employee-pay-cycle notebook runs
- **THEN** its ablation studies section compares manual threshold baselines, classification, regression, expected-value, ranking, ML-only, and final active ranking methods using review-budget metrics, PR-AUC, rank metrics, exposure capture, and dollar capture where available

#### Scenario: Ablation section explains complexity value
- **WHEN** a reviewer reads the ablation studies section of the active employee-pay-cycle notebook
- **THEN** narrative text explains what each formulation level adds, where complexity improves review prioritization, and where simpler methods remain useful

### Requirement: Incremental value plots
The active employee-pay-cycle notebook SHALL include plot-ready evidence that makes incremental method value observable inside the main narrative or technical appendix.

#### Scenario: Method-complexity visuals render
- **WHEN** the active employee-pay-cycle notebook runs
- **THEN** it renders visuals or tables such as an incremental complexity waterfall, component comparison heatmap, precision or exposure by review budget, and threshold-miss or false-positive summaries

#### Scenario: Temporal and uncertainty context remain visible
- **WHEN** the active employee-pay-cycle notebook reports ablation or model comparison results
- **THEN** it includes temporal validation context and uncertainty, stability, or risk-coverage diagnostics where active pipeline outputs support them

### Requirement: Utility-aware employee-cycle evaluation
The employee-pay-cycle evaluation workflow SHALL report business-value metrics based on an explicit `net_utility` label in addition to anomaly-capture and dollar-capture metrics.

#### Scenario: Net utility is reported at review budgets
- **WHEN** employee-pay-cycle review-budget metrics are computed
- **THEN** the outputs include utility-aware summaries such as net utility captured at K, average utility per reviewed employee-pay-cycle, or equivalent project-defined business-value metrics sourced from `net_utility`

#### Scenario: Utility remains evaluation-only
- **WHEN** `net_utility` is available in the scored evaluation frame
- **THEN** it is treated as evaluation-only business truth rather than as an analyst-facing queue field or model input
