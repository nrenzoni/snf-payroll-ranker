## Context

The repository's active runtime, architecture docs, and decision log now center employee-pay-cycle scoring, grouped queue evaluation, and production-candidacy analysis. The active notebook contract has not caught up: current specs still require a multi-notebook sequence, some requirements still assume a separate technical validation notebook, and much of the deeper notebook evidence is implemented only in deprecated shift-level notebook helpers.

This change replaces the old reporting contract with one primary employee-pay-cycle notebook that acts as the active narrative and technical validation surface for residual payroll review after hard rules. The notebook must remain Jupytext-first, fast-mode executable, and grounded in runtime artifacts that are leakage-safe and consistent with the employee-pay-cycle scoring path.

## Goals / Non-Goals

**Goals:**
- Replace sequence-based active notebook requirements with one primary employee-pay-cycle notebook and one fixed section mapping.
- Keep notebook reproducibility, fast validation, and Jupytext source-of-truth behavior intact while changing the reporting contract.
- Align the notebook with active runtime outputs, including hard-rule gating, residual employee-pay-cycle scoring, grouped ranking metrics, review queues, facility summaries, and production-candidacy evidence.
- Define and implement explicit employee-pay-cycle label artifacts for latent residual issue truth, residual dollar impact, dominant category, graded ranking relevance, severe rule-missed issue analysis, and business review utility.
- Close active-runtime gaps that would make the notebook misleading, especially evaluation-truth leakage in employee-cycle formulations and miswired employee-cycle pipeline artifacts.
- Port or rebuild enough diagnostics and stress-evaluation helpers so the notebook's deep-diagnostic and appendix sections are sourced from active employee-cycle outputs rather than deprecated shift-level paths.
- Exclude compliance, PBJ, and HPRD staffing metrics from notebook features, targets, and evaluation so the notebook remains focused on payroll financial leakage and correction risk.

**Non-Goals:**
- Refresh or modernize the deprecated legacy notebook sequence beyond clearly marking it as historical reference.
- Introduce backward-compatibility shims that preserve the old active sequence contract in parallel with the new notebook.
- Claim that every appendix artifact must become a new public runtime API; some appendix assembly may remain notebook-owned if it does not belong in downstream runtime contracts.
- Optimize the hard rules themselves, rank all payroll records before the hard-rule gate, evaluate a full hybrid production policy end to end, or cover regulatory staffing/compliance workflows.

## Decisions

### Decision: Replace the active notebook sequence contract rather than maintain dual contracts
The change will update specs and docs so the single active notebook becomes the only active reporting contract. This avoids contradictory acceptance criteria where one document points to employee-pay-cycle research and another still requires sequence-era shift-level notebook structure.

Alternatives considered:
- Keep both contracts during migration: rejected because it preserves spec ambiguity and forces implementation to satisfy incompatible notebook shapes.
- Add the new notebook without changing old requirements: rejected because it would make the new notebook non-normative.

### Decision: Keep one notebook with a fixed main narrative and appendix sections
The notebook will keep the exact section order requested by the user, with section `11. Technical Appendix` holding dense evidence that previously lived across separate technical and stress notebooks. This preserves a single entry point while still separating the main residual-ranking narrative from deep evidence.

Alternatives considered:
- Keep a separate appendix notebook: rejected because it recreates the split-notebook contract.
- Compress deep diagnostics into the main narrative: rejected because it would weaken readability and conflict with proof-first presentation goals.

### Decision: Treat critical hard rules as an upstream gate and compare only ML models on the residual universe
The notebook should define a critical hard-rule gate that removes obvious payroll problems before any ML comparison begins. The notebook's central experiment is then restricted to the residual universe: employee-pay-cycle records not flagged by critical hard rules, ranked within facility-by-payroll-cycle groups.

The hard rules are part of workflow definition, not a competing model in the `Model Formulations` section. Soft warning signals such as overtime above threshold, manual edits, missing punches, unusual facility patterns, pay-rate changes, and high gross pay versus employee baseline remain eligible as ML features because they are ambiguous residual risk indicators rather than gating conditions.

Alternatives considered:
- Compare hard rules against ML inside the formulation section: rejected because it answers a different question and muddies the stage-2 objective.
- Rank all payroll records end to end: rejected because the user explicitly wants the notebook to measure ML value after obvious cases have already been removed.

### Decision: Source the notebook from active employee-pay-cycle artifacts first, then add notebook-owned assembly only where runtime APIs are too narrow
The notebook should rely on `run_employee_cycle_pipeline()` and related active helpers for its default evidence. When a section needs derived comparisons or plot-ready tables that do not belong in downstream runtime contracts, notebook-owned helper code under `notebooks/` may assemble them from active Polars DataFrames.

Alternatives considered:
- Reuse legacy shift-level notebook helpers directly: rejected because they encode deprecated assumptions and would make the active notebook depend on historical paths.
- Force every appendix artifact into the runtime package first: rejected because some presentation-specific reshaping belongs in notebook code, not the library.

### Decision: Fix active employee-cycle contract gaps before notebook claims depend on them
The current employee-cycle implementation has three material issues:
- the scorer uses `anomaly_dollars` inside the employee-cycle regression-style formulation,
- employee-cycle pipeline artifact wiring returns empty uncertainty and risk-coverage outputs and misroutes production-candidacy data into expected-interval artifacts,
- queue simulation and many repeated-world diagnostic helpers still run through deprecated shift-level paths.

It also lacks the explicit residual-gating and label artifacts that the notebook currently implies exist for learning-to-rank and business-value evaluation. The change will therefore define deterministic employee-cycle label engineering for residual `y_issue`, residual `y_dollar`, `relevance_grade`, `rule_missed_severe_issue`, and `net_utility` rather than treating those as notebook-only concepts.

These issues will be treated as part of the notebook-contract change because the new notebook would otherwise institutionalize incorrect or legacy-only evidence.

Alternatives considered:
- Document the gaps and leave the notebook partially placeholder-driven: rejected because the resulting contract would not be credible.
- Hide unsupported sections: rejected because the user requested fixed section mapping and appendix coverage.

### Decision: Update specs by modifying active capabilities and adding one notebook-specific capability
The spec layer will add `employee-cycle-notebook-reporting` for the fixed notebook structure and appendix requirements, while modifying existing notebook reproducibility, evaluation, review-queue, synthetic-data, and scoring capabilities to remove sequence assumptions and point their notebook obligations to the single active notebook.

Alternatives considered:
- Put every requirement into the new notebook-specific capability only: rejected because evaluation, scoring, and data-generation specs already own notebook-facing acceptance criteria that would otherwise become inconsistent.

### Decision: Use deterministic residual-aware synthetic label formulas for ranking and utility
The change will define explicit residual labels on top of the active employee-pay-cycle anomaly fields.

- `y_issue` is the latent residual issue truth used by the classifier family.
  - `1`: the record remains after the critical hard-rule gate and still contains a latent payroll issue.
  - `0`: the record remains after the gate and has no latent payroll issue.
- `y_dollar` is the residual dollar-impact target used by regression-style models.
  - It represents the synthetic financial impact associated with unresolved residual issues.
- `relevance_grade` is a 0-3 evaluation label for ranking research.
  - `0`: no latent residual issue in the employee-pay-cycle.
  - `1`: minor residual issue.
  - `2`: material residual issue.
  - `3`: severe rule-missed residual issue.
- `rule_missed_severe_issue` is a binary evaluation slice used to measure how well ML recovers severe issues that the hard-rule gate did not catch.
- `net_utility` is a per-reviewed-record business-value label used only for evaluation. It represents recovered synthetic value minus review cost under configurable assumptions rather than a production-visible feature.

The exact cut points and utility assumptions should be deterministic, documented in the notebook, and implemented in runtime code so the ranker and utility evaluation use the same contract.

Alternatives considered:
- Keep `relevance_grade` and `net_utility` as descriptive notebook concepts only: rejected because it makes the notebook misleading.
- Learn utility directly from `anomaly_dollars` without a declared contract: rejected because it hides business assumptions and makes validation harder.
- Mix observed historical review labels into `y_issue`: rejected because the user wants `y_issue` to reflect latent residual issue truth rather than inherited review bias.

## Risks / Trade-offs

- [Deep-diagnostic sections require more than notebook reshuffling] -> Mitigation: treat employee-cycle diagnostic and stress helpers as first-class implementation tasks before notebook assembly.
- [Spec replacement touches multiple active capabilities and can drift if edited partially] -> Mitigation: change all listed capabilities in one OpenSpec change and explicitly remove sequence-era wording from docs at the same time.
- [Single notebook may become heavy to execute] -> Mitigation: preserve fast-mode execution, keep dense appendix workloads bounded in fast mode, and confine expensive repeated-world diagnostics to reduced representative settings when `NOTEBOOK_FAST=1`.
- [Legacy notebook references may continue to confuse contributors] -> Mitigation: update README and `notebooks/README.md` to mark the new notebook as the only active contract and mark legacy notebooks as historical reference only.
- [Appendix asks for artifacts not yet available in active runtime] -> Mitigation: separate runtime-owned evidence from notebook-owned assembly and explicitly implement the missing active diagnostics needed for calibration, stress grids, and facility diagnostics.
- [Residual-only framing can drift back toward broad SNF staffing narratives] -> Mitigation: explicitly exclude compliance, PBJ, and HPRD metrics from change specs, notebook text, and feature lists.
