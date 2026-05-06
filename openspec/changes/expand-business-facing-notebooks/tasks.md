## 1. Baseline Context And Reusable Outputs

- [ ] 1.1 Review existing notebook, pipeline, chart, evaluation, validation, and explainability modules to identify reusable outputs and any small presentation gaps.
- [ ] 1.2 Ensure the pipeline returns or exposes all outputs needed by notebooks, including backtest metrics, scored records, review queue, model comparison, category error analysis, validation outputs, and synthetic payroll data.
- [ ] 1.3 Add minimal helper functions only if needed for notebook presentation, such as schema dictionary rows, compact case-card tables, or missing chart helpers.

## 2. Problem Framing And Data Maturity Notebook

- [ ] 2.1 Create `notebooks/01_problem_framing_and_data_maturity.py` in Jupytext percent format with an executive takeaway and synthetic-data privacy and governance section.
- [ ] 2.2 Add business framing that explains pre-finalization payroll review prioritization, review capacity focus, missed costly exception reduction, and the fact that outputs are not fraud determinations.
- [ ] 2.3 Add the payroll anomaly taxonomy with examples for duplicate payments, overtime spikes, pay after termination, gross pay spikes, incorrect pay rates, missing deductions, negative net pay, retro outliers, department payroll spikes, and unusual new employee payments.
- [ ] 2.4 Add a schema/data dictionary table with field name, business meaning, type or category, privacy sensitivity, and validation expectation.
- [ ] 2.5 Demonstrate validation hard failures versus payroll exception warnings using `validate_payroll` outputs.
- [ ] 2.6 Add data quality summaries for row counts, pay periods, employees, missing values, lifecycle checks, pay distributions, and exception warning counts.
- [ ] 2.7 Add required data maturity visuals or tables, including payroll trend, gross pay distribution, overtime distribution, and department payroll heatmap or table.
- [ ] 2.8 End with a concise what-this-proves summary.

## 3. Feature Engineering And Baselines Notebook

- [ ] 3.1 Create `notebooks/02_feature_engineering_and_baselines.py` in Jupytext percent format with an executive takeaway.
- [ ] 3.2 Demonstrate employee-history features, peer-relative features, rule-based flags, and robust statistical features on concrete synthetic records.
- [ ] 3.3 For selected flagged records, show current gross pay, prior rolling median, percentage change, peer median, peer deviation, rule reason codes, and component scores.
- [ ] 3.4 Explain leakage-safe feature construction and why injected labels are not used as features.
- [ ] 3.5 Compare rule score, statistical score, ML score, and hybrid score as baseline ranking signals using existing model comparison outputs.
- [ ] 3.6 Add a simple gross-pay-change or dollar-impact baseline only if existing outputs do not sufficiently support the baseline comparison narrative.
- [ ] 3.7 Include score distribution and selected employee history visuals.
- [ ] 3.8 End with a concise what-this-proves summary.

## 4. Modeling, Evaluation, And Error Analysis Notebook

- [ ] 4.1 Create `notebooks/03_modeling_evaluation_and_error_analysis.py` in Jupytext percent format with an executive takeaway.
- [ ] 4.2 Explain temporal validation and avoid random train/test split framing.
- [ ] 4.3 Present review-budget metrics including precision@K, recall@K, F1@K, PR-AUC, average anomaly rank, mean reciprocal rank, and dollars-at-risk captured@K.
- [ ] 4.4 Show model comparison for rule score, statistical score, ML score, and hybrid score.
- [ ] 4.5 Explain why hybrid ranking fits payroll review better than a single score source.
- [ ] 4.6 Show precision@K and dollars captured@K visuals by review budget.
- [ ] 4.7 Show backtest-by-period results and a backtest-over-time visual or table.
- [ ] 4.8 Show category-level error analysis and include cost-aware interpretation of review budgets and precision drop-offs.
- [ ] 4.9 End with a concise what-this-proves summary.

## 5. Review Queue, Explainability, And Thresholds Notebook

- [ ] 5.1 Create `notebooks/04_review_queue_explainability_and_thresholds.py` in Jupytext percent format with an executive takeaway.
- [ ] 5.2 Display an analyst-readable review queue with reason codes, explanations, risk categories, and review-safe language.
- [ ] 5.3 Create compact case cards for selected records with rank, employee ID, pay period, risk category, primary reason, secondary reason, expected gross pay, actual gross pay, difference from expected, peer context, dollars at risk, and explanation.
- [ ] 5.4 Demonstrate choosing alert thresholds or top-K review budgets and show expected queue size per pay period.
- [ ] 5.5 Explain high, medium, and low risk categories and practical analyst next actions.
- [ ] 5.6 Add a concise payroll analyst operating model for triage, approval, escalation, and feedback.
- [ ] 5.7 Describe how analyst feedback would be captured conceptually without implementing a case management integration.
- [ ] 5.8 End with a concise what-this-proves summary.

## 6. Production Monitoring And Deployment Path Notebook

- [ ] 6.1 Create `notebooks/05_production_monitoring_and_deployment_path.py` in Jupytext percent format with an executive takeaway.
- [ ] 6.2 Document a realistic deployment path using payroll, HRIS, and timekeeping extracts, validation, feature generation, scoring, review queue export, analyst feedback, monitoring, and retraining.
- [ ] 6.3 Include an architecture diagram section or structured architecture table without claiming live integrations are implemented.
- [ ] 6.4 Include monitoring metrics for alert count per cycle, alert acceptance rate, false positive rate from reviews, dollars at risk flagged and confirmed, feature drift, score drift, alert concentration by department/location/job family, latency, data freshness, and failed validation count.
- [ ] 6.5 Include retraining triggers for drift, business rule changes, payroll calendar changes, degraded review outcomes, and enough reviewed labels for supervised calibration.
- [ ] 6.6 Include limitations and risks covering simplified synthetic labels, legitimate bonuses or high earners flagged by unsupervised scores, required human review, and threshold calibration.
- [ ] 6.7 End with a concise what-this-proves summary.

## 7. Index Notebook And README

- [ ] 7.1 Shorten or revise `notebooks/payroll_anomaly_detection.py` into an index/overview notebook that links the notebook sequence together, if practical.
- [ ] 7.2 Update `README.md` to list the notebook sequence and briefly explain each notebook purpose.

## 8. Verification

- [ ] 8.1 Run formatting or notebook smoke checks available in the repository.
- [ ] 8.2 Run the test suite or existing smoke tests with `uv`.
- [ ] 8.3 Run or smoke-execute the notebook sequence from a clean checkout path to confirm synthetic data and outputs are generated or reused under `data/synthetic` and `outputs/evaluation`.
- [ ] 8.4 Verify all notebooks use Jupytext percent format and avoid real or sensitive data and fraud-determination language.
