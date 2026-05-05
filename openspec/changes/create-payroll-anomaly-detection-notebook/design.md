## Context

The project should present payroll anomaly detection as an operational review-queue problem, not as unsupported fraud detection. Payroll data is highly sensitive, so the implementation will use only synthetic employee-pay-period data and will explicitly document that no real identifiers, salaries, tax information, banking details, HR comments, or company-specific records are included.

The repository should support both a readable notebook deliverable and modular source files so the work looks reproducible and production-oriented. The notebook should communicate to technical and semi-technical reviewers: privacy maturity, domain judgment, leakage-aware feature engineering, model comparison, evaluation despite sparse labels, explainable outputs, and production monitoring considerations.

## Goals / Non-Goals

**Goals:**

- Build a synthetic payroll dataset at employee-pay-period grain with realistic compensation, overtime, deduction, lifecycle, department, role, location, bonus, commission, retro pay, and manual adjustment patterns.
- Inject labeled anomaly categories so the notebook can evaluate detection quality without using sensitive real data.
- Create leakage-safe historical, peer-relative, rule-based, robust statistical, and ML anomaly features and scores.
- Compare deterministic rules, robust statistics, Isolation Forest, and a configurable hybrid score.
- Optimize and report review-queue metrics such as precision@K, recall@K, dollars-at-risk captured@K, and category-level performance under temporal validation.
- Produce an analyst-ready review queue with explanations, risk categories, dollars at risk, and supporting feature context.
- Include data quality checks, privacy guardrails, limitations, production architecture, monitoring, retraining, and future improvements in the notebook and README.

**Non-Goals:**

- Do not use, publish, or require real payroll, HR, tax, banking, employee, manager, or company-specific data.
- Do not claim production integration with payroll vendors, HRIS, ERP, or timekeeping systems.
- Do not build a live dashboard, alerting service, role-based access control, or scheduled batch job in the initial MVP.
- Do not present unsupervised scores as confirmed fraud labels.
- Do not include neural-network models unless they are justified by later scope and evaluation needs.

## Decisions

1. Use employee-pay-period as the primary unit of analysis.

   Rationale: This grain is intuitive for payroll review, supports employee history and peer comparisons, and maps naturally to payroll operations deciding which employee-period records require pre-finalization review. Transaction-level records were considered, but they add accounting complexity that is not needed for the first deliverable.

2. Generate synthetic data and injected labels instead of sourcing public or real payroll records.

   Rationale: Synthetic data demonstrates privacy judgment and enables controlled evaluation. Public payroll datasets often lack the sensitive operational fields needed for anomaly detection, while real payroll data would create unacceptable privacy and re-identification risk.

3. Implement a layered hybrid anomaly architecture.

   Rationale: Payroll anomalies include deterministic policy violations, statistical outliers, peer-relative deviations, and multivariate patterns. A hybrid score combining rule severity, employee-history scores, peer-group scores, Isolation Forest scores, and dollar-impact weighting is more credible than a single unsupervised model. Weights should be configurable and selected from validation results rather than presented as universal constants.

4. Compute historical features using prior periods only.

   Rationale: Payroll modeling is prone to lookahead leakage. Rolling means, medians, standard deviations, percent changes, and peer baselines must be shifted or otherwise computed from records available before the scored pay period.

5. Use temporal and backtesting-style evaluation.

   Rationale: Random row splits leak future behavior and overstate performance. The notebook should train/tune on earlier pay periods and score later periods, reporting review-queue metrics per period and overall.

6. Prioritize explainability and review queue outputs.

   Rationale: Payroll teams need actionable records with reasons, not just model scores. Every top-ranked record should include a risk category, primary and secondary reasons, relevant rule flags, expected value context, peer percentile or baseline comparison, and estimated dollars at risk.

7. Keep implementation modular but notebook-first.

   Rationale: A polished notebook is the primary deliverable, while source modules for data generation, features, rules, models, evaluation, and explainability demonstrate engineering discipline and make the notebook reproducible.

## Risks / Trade-offs

- Synthetic data may look unrealistic or too clean -> Mitigate with skewed pay distributions, seasonal effects, promotions, terminations, department variation, hourly/salaried differences, manual adjustments, missingness, and realistic anomaly overlap.
- Injected anomalies may make evaluation easier than real operations -> Mitigate by documenting limitations, adding subtle anomaly types, reporting category-level misses, and describing analyst feedback as the path to supervised improvement.
- Hybrid scoring weights may appear arbitrary -> Mitigate by using validation-set ranking metrics to compare candidate weights and documenting them as configurable business parameters.
- Too many notebook sections may reduce readability -> Mitigate with an executive summary, clear narrative flow, concise charts, and modular source files for implementation details.
- Isolation Forest can flag high earners or legitimate bonuses as anomalies -> Mitigate with peer grouping, bonus season features, rule explanations, error analysis, and cost/review-budget thresholding.
- Data quality checks may conflict with valid payroll exceptions -> Mitigate by distinguishing hard validation failures from warning checks and documenting examples such as corrections, retro pay, and approved bonuses.
