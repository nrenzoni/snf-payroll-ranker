## Context

The repository already implements the core payroll anomaly ranking pipeline in reusable Python modules: synthetic data generation, validation, leakage-safe features, deterministic rules, statistical and Isolation Forest scoring, hybrid ranking, evaluation, explainability, and basic chart helpers. The current `notebooks/payroll_anomaly_detection.py` is a compact overview that mentions these capabilities but does not demonstrate them deeply enough for a business-facing case study.

The change should preserve the notebook-library pattern and Jupytext percent-format workflow. The primary stakeholders are reviewers, payroll analysts, data science evaluators, and maintainers who need a clear demonstration that the system ranks synthetic payroll records for pre-finalization review without claiming fraud determination or live production integration.

## Goals / Non-Goals

**Goals:**

- Add five focused Jupytext-paired notebooks that tell a complete payroll anomaly ranking story from business framing through deployment path.
- Reuse existing `payroll_anomaly_ranking` modules for generation, validation, features, rules, models, evaluation, explainability, and charts.
- Demonstrate privacy and governance, data dictionary, validation outputs, data quality summaries, leakage-safe features, baseline and hybrid scoring, temporal evaluation, review queues, explainability, threshold selection, operating model, monitoring, retraining triggers, and limitations.
- Include clear visuals and tables suitable for business review.
- Update `README.md` to make the notebook sequence discoverable.
- Keep implementation runnable from a clean checkout with `uv` and Jupytext.

**Non-Goals:**

- Do not introduce real payroll, HRIS, timekeeping, bank, tax, employee, or company data.
- Do not build or claim live integrations, orchestration, alert delivery, case management, or production retraining.
- Do not convert the project into a supervised fraud detection system.
- Do not add large new modeling frameworks or broad data model changes.

## Decisions

1. Split the story into five notebooks instead of expanding one large notebook.

   Rationale: the requested topics span business framing, data maturity, feature engineering, evaluation, explainability, and production thinking. Separate notebooks make the case study easier to review and rerun in stages.

   Alternative considered: one comprehensive notebook. Rejected because it would be harder to navigate and would preserve the current problem of a compressed demonstration.

2. Use the existing pipeline outputs as the shared demonstration substrate.

   Rationale: `run_pipeline` already writes synthetic data and evaluation artifacts under the expected output paths. The notebooks should showcase the implemented code rather than duplicating pipeline logic.

   Alternative considered: each notebook rebuilding custom data flows independently. Rejected because it would increase maintenance cost and risk inconsistencies between notebooks.

3. Keep helper additions minimal and presentation-focused.

   Rationale: most required behavior exists. Any additions should support notebook readability, such as schema/data dictionary tables, case-card shaping, or exposing already-computed backtest outputs to notebooks.

   Alternative considered: building a separate notebook helper package. Rejected unless repeated code becomes materially complex during implementation.

4. Preserve business-safe language throughout the notebooks.

   Rationale: payroll anomaly ranking prioritizes records for analyst review. The notebooks must avoid presenting outputs as fraud determinations and should use language such as exception, triage, requires review, and analyst review.

   Alternative considered: fraud-oriented language for stronger narrative impact. Rejected because it overstates the system and creates governance risk.

5. Treat temporal validation as the only evaluation framing.

   Rationale: payroll records are time-dependent and employee histories can leak information. The notebooks should explain that labels are retained for evaluation only and are not used as scoring features.

   Alternative considered: random train/test split examples. Rejected because they conflict with the existing specs and can mislead reviewers.

## Risks / Trade-offs

- Notebook runtime could become slow if every notebook regenerates and rescans the full dataset → Use moderate default `PayrollConfig` sizes and reuse persisted outputs where practical.
- Repeated setup code across notebooks could become noisy → Keep common setup concise and only add a shared helper if duplication becomes distracting.
- Business-facing visuals may need more polish than existing chart helpers provide → Prefer existing helpers first and add only minimal chart helpers for required visuals not already covered.
- Synthetic labels and injected anomalies may appear more orderly than real payroll exceptions → Explicitly document this limitation and frame results as demonstration evidence, not production performance guarantees.
- Unsupervised scores can flag legitimate bonuses, high earners, or seasonal pay patterns → Include limitations, analyst review workflow, and threshold calibration guidance.
