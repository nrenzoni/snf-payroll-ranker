## MODIFIED Requirements

### Requirement: Technical ML value and ablation notebook
The active employee-pay-cycle notebook SHALL include sections that demonstrate incremental residual-formulation value using evaluation-safe synthetic labels and temporal validation framing.

#### Scenario: Ablation section compares method ladder
- **WHEN** the active employee-pay-cycle notebook runs
- **THEN** its ablation studies section compares classifier, cost-sensitive classifier, regressor, expected-value, and learning-to-rank methods on the residual universe using residual review-budget metrics, PR-AUC where applicable, rank metrics, dollar capture, reviewer yield, and utility metrics where available

#### Scenario: Ablation section explains complexity value
- **WHEN** a reviewer reads the ablation studies section of the active employee-pay-cycle notebook
- **THEN** narrative text explains what each residual formulation adds, where complexity improves residual review prioritization, and where simpler methods remain useful

### Requirement: Incremental value plots
The active employee-pay-cycle notebook SHALL include plot-ready evidence that makes incremental method value observable inside the main narrative or technical appendix.

#### Scenario: Method-complexity visuals render
- **WHEN** the active employee-pay-cycle notebook runs
- **THEN** it renders visuals or tables such as residual dollars caught by review budget, rule-missed severe recall by review budget, residual NDCG by review budget, reviewer yield by review budget, net utility by review budget, and compact formulation-comparison summaries

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

### Requirement: Residual-universe queue metrics
The employee-pay-cycle evaluation workflow SHALL compute primary notebook metrics only on residual records within facility-by-payroll-cycle groups.

#### Scenario: Residual metrics use gated scoring universe
- **WHEN** the notebook reports main queue results
- **THEN** ranking and review-budget metrics are computed only on employee-pay-cycle records not flagged by critical hard rules
- **AND** the ranking groups are facility by payroll cycle

#### Scenario: Primary residual metrics are reported
- **WHEN** residual review-budget metrics are computed
- **THEN** the outputs include residual NDCG@K, rule-missed severe recall@K, residual dollars caught@K, reviewer yield@K, and incremental utility@K or equivalent project-defined formulations of those metrics

### Requirement: Training-universe and label ablations
The active employee-pay-cycle notebook SHALL test whether residual-ranking conclusions depend on label choice or training universe definition.

#### Scenario: Training-universe ablation is shown
- **WHEN** the ablation studies section is reviewed
- **THEN** it compares training on all records, training on residual records only, and training on all records with hard-rule flag features while always scoring on the residual universe

#### Scenario: Label ablation is shown
- **WHEN** the ablation studies section is reviewed
- **THEN** it compares formulations trained or evaluated against binary issue, dollar impact, graded relevance, utility-aware, observed historical, or latent truth labels where those comparisons are supported by active outputs
