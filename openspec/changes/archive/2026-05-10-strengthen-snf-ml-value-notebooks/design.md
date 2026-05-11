## Context

The existing notebook sequence already covers feature engineering, modeling evaluation, queue explainability, monitoring, internal diagnostics, and queue simulation. `notebooks/08_snf_payroll_approval_case_studies.py` is the natural business-facing capstone for SNF payroll approval, but it currently relies mostly on tables and does not clearly show why automated hybrid ranking improves on manual thresholds. The project also has enough evaluation and diagnostic outputs to support a separate technical notebook that demonstrates method-complexity value through ablation, temporal validation, uncertainty, and robustness evidence.

The implementation must preserve the project's current boundaries: Jupytext `.py` files are source of truth, notebook visuals use Lets-Plot, production package code remains free of notebook-only plotting dependencies, and analyst-safe queues must not expose synthetic evaluation truth.

## Goals / Non-Goals

**Goals:**

- Turn notebook 08 into a clear SNF administrator/business proof of value with narrative before and after major tables and plots.
- Add a technical validation notebook that demonstrates why the hybrid method earns its complexity compared with manual thresholds, rules, robust statistics, and ML-only scoring.
- Reuse existing pipeline outputs where practical: `metrics`, `model_comparison`, `threshold_baseline_metrics`, `category_error_analysis`, `rolling_origin_metrics`, uncertainty outputs, facility approval summaries, analyst queues, and diagnostic helpers.
- Keep synthetic labels and injected anomaly dollars restricted to explicitly evaluation-labeled sections, with business-facing case cards using review-safe language.
- Keep notebook validation practical by supporting `NOTEBOOK_FAST=1` when repeated pipeline runs or dense diagnostics are used.

**Non-Goals:**

- Do not add new production integrations with payroll, HRIS, timekeeping, scheduling, or EHR systems.
- Do not claim confirmed fraud detection, confirmed misconduct, or confirmed payroll error.
- Do not introduce new ML libraries or notebook plotting dependencies.
- Do not redesign the scoring model or change persisted output contracts unless a small helper output is required for notebook evidence.
- Do not refresh paired `.ipynb` artifacts unless explicitly requested.

## Decisions

1. Split the audience into two notebooks.

   Notebook 08 remains business-facing and focuses on SNF payroll approval workflow, manual threshold limitations, administrator-safe queues, facility summaries, and case cards. A new notebook 09 focuses on ablation and technical validation. This avoids overloading one notebook with both executive workflow and data-science diagnostics.

   Alternative considered: keep all content in notebook 08. This was rejected because the notebook would become too long and would dilute both the administrator narrative and the technical validation narrative.

2. Use one OpenSpec change for both notebooks.

   The two notebooks are one evidence package: notebook 08 proves operational value, and notebook 09 validates the modeling choices. Keeping them in one change keeps requirements, implementation, and verification aligned.

   Alternative considered: separate business and technical validation changes. This is only useful if implementation must be phased separately; otherwise it creates duplicated context and weakens the end-to-end story.

3. Prefer notebook-local shaping over new package APIs.

   Most evidence can be produced from existing result DataFrames. Notebook-local Polars transformations are acceptable for plot-specific shaping. Shared `notebooks/common/` helpers should only be added when the same transformation or plotting pattern is reused enough to improve readability.

   Alternative considered: add new production package evaluation APIs for every plot. This was rejected to avoid expanding public contracts for presentation-only needs.

4. Show a method-complexity ladder rather than presenting ML as a black box.

   The technical notebook should compare manual thresholds, deterministic rules, robust statistical scoring, ML scoring, and hybrid ranking. This directly answers whether the additional complexity improves approval-budget metrics, exposure capture, and ranking quality.

   Alternative considered: compare only manual thresholds and final hybrid ranking. This is useful for business users but insufficient for data scientists who need to understand component contribution.

5. Separate business-safe and evaluation-only evidence.

   Notebook 08 should emphasize administrator-safe fields such as primary reason, source to check, recommended action, estimated exposure, expected-vs-actual context, and facility summaries. Notebook 09 may use synthetic labels, injected anomaly categories, and injected anomaly dollars, but only in clearly labeled evaluation sections.

   Alternative considered: include labels in business case-study tables for convenience. This was rejected because it conflicts with review-safe workflow requirements and could encourage overclaiming.

## Risks / Trade-offs

- Sparse or low-variation synthetic outputs could produce weak visuals -> Use diagnostic case-study scenarios, fast-mode scenario reductions only where needed, and plot usefulness checks or fallback tables when a visual lacks variation.
- Notebook runtime could become too slow -> Gate expensive multi-scenario or repeated-origin work behind `NOTEBOOK_FAST`, smaller configs, or existing diagnostic helpers with reduced fast-mode defaults.
- Business notebook could accidentally expose evaluation truth -> Explicitly select administrator-safe columns in notebook 08 and reserve synthetic-label fields for notebook 09 evaluation sections.
- Technical notebook could duplicate notebooks 03, 06, and 07 -> Position notebook 09 as a focused ablation and incremental-ML-value story, borrowing selected ideas rather than recreating every diagnostic.
- New visuals could add brittle plotting code -> Keep plot inputs tidy, use existing column constants, and prefer simple Lets-Plot charts with clear narrative interpretation.
