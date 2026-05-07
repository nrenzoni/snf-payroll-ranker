## ADDED Requirements

### Requirement: Internal Bayesian-style review-budget diagnostics
The system SHALL provide internal statistical uncertainty diagnostics for review-budget metrics without changing analyst-facing queue behavior.

#### Scenario: Review-budget credible intervals are reported
- **WHEN** internal statistical diagnostics run against evaluation-labeled scored records
- **THEN** the output includes interval summaries for Precision@25, Recall@25, dollars captured@25, and dollar capture rate using Bayesian bootstrap, Beta-Binomial posterior intervals, bootstrap posterior simulation, or equivalent closed-form/posterior-simulation methods

#### Scenario: Component score superiority is summarized
- **WHEN** internal diagnostics compare hybrid, rule, statistical, ML, and exposure-based rankings
- **THEN** the output estimates the probability or frequency that one ranking signal outperforms another on configured review-budget metrics across seeds, origins, or bootstrap samples

#### Scenario: Full MCMC is not required for baseline diagnostics
- **WHEN** Bayesian-style internal diagnostics are implemented
- **THEN** the baseline implementation uses closed-form, empirical-Bayes, bootstrap, or posterior-simulation methods and does not require PyMC, Stan, or another full MCMC dependency

#### Scenario: Metrics remain evaluation-only
- **WHEN** internal Bayesian-style diagnostics use injected labels or injected anomaly dollar impacts
- **THEN** the outputs are marked or scoped as internal evaluation diagnostics and do not alter analyst-safe review queue fields

### Requirement: Hierarchical subgroup diagnostics
The system SHALL provide internal subgroup diagnostics with shrinkage-aware summaries for payroll hierarchy dimensions.

#### Scenario: Subgroup diagnostic table is produced
- **WHEN** internal subgroup diagnostics run
- **THEN** the output summarizes review quality, anomaly concentration, false positives, false negatives, uncertainty, and sample size by dimensions such as department, job family, location, pay type, pay code, or job level

#### Scenario: Shrinkage diagnostics distinguish raw and pooled estimates
- **WHEN** subgroup sample sizes vary materially
- **THEN** the output includes raw subgroup estimates and empirical-Bayes or partial-pooling estimates so sparse groups are not overinterpreted

#### Scenario: Full hierarchical Bayesian model is optional
- **WHEN** subgroup diagnostics are implemented
- **THEN** empirical-Bayes or partial-pooling summaries satisfy the baseline requirement, while a full MCMC hierarchical model MAY be added later as a non-blocking enhancement

#### Scenario: Hierarchical plots render from diagnostic outputs
- **WHEN** the internal statistical diagnostics notebook runs
- **THEN** it displays subgroup forest, caterpillar, shrinkage, or funnel plots from the generated diagnostic tables

### Requirement: Expected-pay calibration diagnostics
The system SHALL evaluate expected gross-pay interval calibration in internal diagnostics.

#### Scenario: Expected-pay coverage is summarized by subgroup
- **WHEN** expected gross-pay interval fields are present
- **THEN** internal diagnostics summarize empirical interval coverage, interval width, and excess over expected p90 overall and by selected subgroup dimensions

#### Scenario: Calibration plots render from expected-pay diagnostics
- **WHEN** the internal statistical diagnostics notebook runs with expected-pay interval outputs
- **THEN** it displays actual-versus-expected, coverage, residual, or percentile calibration plots for expected gross-pay behavior

### Requirement: Robustness and perturbation diagnostics
The system SHALL provide internal robustness diagnostics for seeds, temporal origins, parameter choices, queue overlap, and local score sensitivity.

#### Scenario: Stability outputs include queue overlap
- **WHEN** robustness diagnostics run across seeds, temporal origins, or configured parameter choices
- **THEN** the output includes metric distributions and top-queue overlap summaries for configured review budgets

#### Scenario: Performance-instability tradeoff is reported
- **WHEN** multiple parameter or scenario settings are evaluated
- **THEN** the output supports comparison of mean performance against instability using tables or plots such as heatmaps or Pareto views

#### Scenario: Local perturbation sensitivity is reported
- **WHEN** perturbation diagnostics run for selected records or feature families
- **THEN** the output summarizes how score, rank, or threshold-crossing behavior changes under controlled input perturbations

### Requirement: Monte Carlo queue capacity simulation
The system SHALL simulate analyst review capacity and queue outcomes using scored outputs and configured operational assumptions.

#### Scenario: Queue capacity outcomes are summarized
- **WHEN** Monte Carlo queue simulation runs against scored records
- **THEN** the output includes queue size, reviewed records, overload probability, captured anomalies, dollars captured, missed estimated exposure, and missed synthetic anomaly dollars under configured review-capacity assumptions

#### Scenario: Missed exposure fields separate observable and evaluation-only quantities
- **WHEN** queue simulation summarizes missed impact
- **THEN** it reports production-observable missed estimated exposure separately from evaluation-only missed synthetic anomaly dollars

#### Scenario: Scenario stress tests compare queue outcomes
- **WHEN** queue simulation runs across multiple payroll scenarios or drift settings
- **THEN** the output compares review-budget performance, overload risk, and dollar capture across scenarios

#### Scenario: Queue simulation remains downstream of scoring
- **WHEN** queue capacity simulation is configured
- **THEN** it consumes scored payroll outputs or review queues and does not modify source payroll generation, scoring features, or analyst-safe queue leakage rules

### Requirement: Internal statistical notebook coverage
The repository SHALL include internal Jupytext notebooks for statistical diagnostics and simulation stress testing.

#### Scenario: Internal diagnostics notebook renders advanced plots
- **WHEN** the internal statistical diagnostics notebook runs
- **THEN** it displays Bayesian-style metric intervals, hierarchical subgroup diagnostics, expected-pay calibration checks, robustness plots, exposure calibration, and perturbation sensitivity views

#### Scenario: Simulation stress-testing notebook renders scenario plots
- **WHEN** the simulation and stress-testing notebook runs
- **THEN** it displays Monte Carlo queue-capacity outcomes, drift or anomaly-mix scenario comparisons, change-point or drift diagnostics, and stress-test heatmaps

#### Scenario: Business-facing notebooks remain intact
- **WHEN** internal diagnostic notebooks are added
- **THEN** the existing business-facing notebook sequence remains available and is not required to include every internal statistical plot

#### Scenario: Internal notebooks are documented separately
- **WHEN** the README documents notebook coverage
- **THEN** it lists the internal statistical and simulation notebooks separately from the required business-facing notebook sequence

#### Scenario: Internal notebooks execute reproducibly
- **WHEN** documented internal notebook execution commands are run from a clean checkout
- **THEN** the internal notebooks complete without traceback outputs using bounded default simulation counts suitable for local execution
