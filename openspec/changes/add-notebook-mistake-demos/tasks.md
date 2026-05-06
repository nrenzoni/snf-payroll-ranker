## 1. Notebook Structure

- [x] 1.1 Review `notebooks/03_modeling_evaluation_and_error_analysis.py` for the best insertion points after existing temporal validation, model comparison, and cost-aware sections.
- [x] 1.2 Add a concise notebook section introducing common anomaly-modeling evaluation mistakes and how the demos should be interpreted with synthetic labels.
- [x] 1.3 Decide whether repeated demo logic should stay in notebook cells or move to a sibling helper file following the notebook-library pattern.

## 2. Mistake Demonstrations

- [x] 2.1 Add a random train/test split anti-pattern demo and compare it with temporal validation using a plot that shows leakage or overly optimistic evaluation risk.
- [x] 2.2 Add an Isolation Forest default-parameters anti-pattern demo and compare it with an explicit tuned/configured approach using metric and score-distribution plots.
- [x] 2.3 Add a ROC-AUC-only reporting anti-pattern demo and compare it with PR-AUC, Precision@K, review-budget, or rank-based metrics using a plotted comparison.
- [x] 2.4 Add a false-positive neglect anti-pattern demo and compare it with false-positive, false-negative, and review-load analysis using a plot or queue summary.
- [x] 2.5 Add an equal-anomaly-importance anti-pattern demo and compare it with severity, dollar exposure, category, or review-capacity-aware prioritization using a plot.
- [x] 2.6 Add an overclaiming fraud-detection anti-pattern demo and compare it with correct language that frames the output as synthetic anomaly review prioritization.

## 3. Validation

- [x] 3.1 Run the affected Jupytext notebook or equivalent Python execution path to ensure all new cells execute without errors.
- [x] 3.2 Verify every requested mistake has a labeled anti-pattern, a labeled corrected method, and at least one plot or visual comparison.
- [x] 3.3 Verify the final notebook wording avoids claiming confirmed fraud detection and preserves the synthetic-data evaluation caveat.
- [x] 3.4 Run the repository test or smoke-check command used by the project and address any regressions.
