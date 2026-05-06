## Context

The current payroll anomaly workflow is modular and notebook-friendly, with synthetic data generation, feature engineering, rules, scoring, evaluation, explanations, and notebooks under `src/payroll_anomaly_ranking/` and `notebooks/`. It already presents temporal validation, review-budget metrics, model comparison, reason codes, and a production-readiness narrative.

The main weakness is that some demonstration conveniences blur the line between evaluation truth and production-observable scoring inputs. In particular, injected anomaly dollar impact is currently used as a scoring component and appears in the review queue. Some feature baselines also use full-dataset references that are not strictly available at scoring time. This change makes the workflow more credible for advanced data-science review while preserving the existing synthetic demo and notebook sequence.

## Goals / Non-Goals

**Goals:**

- Ensure scoring and analyst-facing outputs do not use injected labels, injected anomaly categories, or injected anomaly dollar impacts.
- Compute history, peer, robust, and ML reference signals in a way that is explainable as available at the scored period.
- Add deterministic missing-deduction rule support so the taxonomy, rules, explanations, and category error analysis align.
- Provide separate operational and evaluation outputs: an analyst-safe queue for review workflow and a labeled queue for synthetic performance analysis.
- Add rolling-origin validation and stability summaries that better reflect future-cycle payroll review.
- Make notebook execution and generated artifacts reproducible enough for a polished case-study deliverable.

**Non-Goals:**

- No live payroll, HRIS, timekeeping, banking, case-management, alerting, or deployment integration.
- No real employee data or production security model.
- No new external modeling dependency unless the existing stack cannot support the requirement.
- No claim that synthetic performance proves confirmed fraud detection or production effectiveness.

## Decisions

### Decision: Replace injected dollar impact with estimated exposure

Use observable payroll fields and leakage-safe baselines to estimate dollars at risk for scoring and analyst review. Candidate inputs include gross pay above expected history, gross pay above peer baseline, extreme overtime excess, manual adjustment magnitude, net/gross inconsistency, missing deductions estimated from prior or peer deduction ratios, and rule severity.

Alternative considered: keep `anomaly_dollars` as `dollar_score` because it is useful for demo performance. Rejected because it is evaluation truth and would not be known before analyst review.

### Decision: Keep injected labels only in evaluation artifacts

The pipeline should produce an analyst-safe queue without `is_anomaly`, `anomaly_category`, or injected `anomaly_dollars`, and a separate evaluation-labeled queue that joins those fields back for synthetic analysis.

Alternative considered: keep one queue and document the labels as synthetic. Rejected because the artifact shape still teaches an unrealistic operational workflow.

### Decision: Make reference features period-aware before expanding model complexity

Feature hardening should focus on temporal correctness first: employee history remains shifted, peer baselines should exclude the current row and future periods where possible, and robust/global statistics should be computed from prior/reference windows rather than all rows being scored.

Alternative considered: add more advanced models immediately. Rejected because additional models would not fix leakage and could make the demo less trustworthy.

### Decision: Add missing-deduction as a deterministic rule

Missing or zero deductions should become an explicit rule flag, severity contributor, reason code, and explanation source. This aligns the supported taxonomy with scoring and improves currently missed category performance.

Alternative considered: let deduction ratio/statistical features catch missing deductions. Rejected because deduction exceptions are deterministic enough to explain directly.

### Decision: Use rolling-origin summaries for advanced evaluation

Evaluation should include multiple train/validation/test cuts by pay period and summarize precision@K, dollar/exposure capture, false positives, false negatives, and score/queue stability across origins. Thresholds or hybrid weights should be selected on validation periods before test-period reporting.

Alternative considered: keep one fixed temporal split. Rejected because it is simpler but does not demonstrate robust future-cycle performance.

### Decision: Treat notebook reproducibility as part of the deliverable

Notebook `.py` and `.ipynb` pairs should execute from a clean checkout without errors and saved outputs should be refreshed consistently. Tests should focus on key invariants rather than snapshotting every rich notebook output.

Alternative considered: leave notebooks as manually run presentation artifacts. Rejected because the repository is notebook-centric and communication quality is part of the evaluation criteria.

## Risks / Trade-offs

- Reduced headline performance after removing label-derived dollar scoring -> Mitigate by explaining that lower metrics are more credible and by reporting both anomaly capture and estimated exposure capture.
- Period-aware peer/robust features may be noisier in early periods -> Mitigate with clear fallback hierarchy from employee history to prior peer/global references and by surfacing baseline source in explanations where useful.
- Separate queue outputs add file/API surface area -> Mitigate with clear names such as `analyst_review_queue.csv` and `evaluation_labeled_review_queue.csv`.
- Rolling-origin validation increases runtime and notebook length -> Mitigate by keeping synthetic defaults modest and summarizing results compactly.
- Notebook reproducibility checks can become brittle -> Mitigate by testing execution success and required output presence rather than exact HTML plot content.

## Migration Plan

- Update scoring/explanation code to produce label-free estimated exposure fields while retaining labels only on the scored evaluation frame.
- Update pipeline outputs to write separate analyst-safe and labeled evaluation queues.
- Update notebooks and README output lists to use the new queue names and explain the distinction.
- Regenerate synthetic outputs and execute notebooks cleanly.
- Run unit tests and notebook execution checks before archiving the change.

Rollback is straightforward because the project uses synthetic generated outputs: revert the scoring/queue code paths and regenerate the prior CSV outputs if needed.

## Open Questions

- What default review budget should drive category error analysis after the queue split: keep 25 or align with the first configured budget?
- Should hybrid weights remain hand-configured after validation-period tuning is added, or should the tuned weights be optional demonstration output only?
- Should notebook execution tests run all notebooks in CI by default or remain a documented local verification command to avoid slower test runs?
