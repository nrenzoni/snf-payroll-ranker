## 1. Leakage-Free Scoring Foundation

- [x] 1.1 Add column definitions for estimated exposure, exposure score, missing-deduction rule flag, and separate analyst/evaluation queue outputs.
- [x] 1.2 Replace `anomaly_dollars`-based scoring with production-observable estimated exposure from expected gross pay, peer context, deduction expectations, overtime excess, manual adjustments, and rule severity.
- [x] 1.3 Add tests proving `is_anomaly`, `anomaly_category`, and `anomaly_dollars` are not used by model feature matrices, exposure scoring, or final hybrid scoring.

## 2. Period-Safe Feature Engineering

- [x] 2.1 Update peer-relative feature construction so scored rows do not use future periods and do not include the scored row in its own peer aggregate where feasible.
- [x] 2.2 Update robust statistical feature construction to use prior or scoring-time-available reference distributions instead of full future-inclusive data.
- [x] 2.3 Add fallback behavior for early pay periods with sparse history or peer references.
- [x] 2.4 Add tests for shifted history, period-safe peer references, robust reference windows, and early-period fallback behavior.

## 3. Deterministic Rule And Explanation Coverage

- [x] 3.1 Add a missing-or-zero deduction deterministic rule flag, severity contribution, and reason code.
- [x] 3.2 Update explanations and case-card language so deduction anomalies can be described directly in payroll terms.
- [x] 3.3 Add tests showing missing-deduction records receive rule flags, reason codes, severity, and review explanations.

## 4. Analyst-Safe And Evaluation-Labeled Queues

- [x] 4.1 Split review queue generation into an analyst-safe queue and an evaluation-labeled queue.
- [x] 4.2 Ensure the analyst-safe queue excludes injected labels, injected anomaly categories, and injected anomaly dollar impacts.
- [x] 4.3 Ensure the evaluation-labeled queue preserves synthetic labels for metrics, category error analysis, and notebook interpretation.
- [x] 4.4 Update pipeline output writing to export both queue artifacts with clear file names.
- [x] 4.5 Add tests for queue field separation, sort order, and review-safe language.

## 5. Advanced Temporal Evaluation

- [x] 5.1 Add rolling-origin evaluation across multiple train/validation/test pay-period cuts when enough periods are available.
- [x] 5.2 Add validation-based threshold or hybrid-weight selection before test-period metric reporting.
- [x] 5.3 Add stability summaries such as metric ranges, score distribution shifts, and queue overlap across origins or seeds.
- [x] 5.4 Add explicit leakage-check outputs that confirm label columns and injected dollar impacts are excluded from scoring and analyst queues.
- [x] 5.5 Add tests for rolling-origin split ordering, validation-selected settings, stability summaries, and leakage-check outputs.

## 6. Notebook And Documentation Updates

- [x] 6.1 Update notebooks to explain label-free exposure scoring, period-safe baselines, missing-deduction rule coverage, queue separation, and rolling-origin validation.
- [x] 6.2 Update notebook tables and visuals to use the new queue artifacts and advanced evaluation outputs.
- [x] 6.3 Update README expected outputs and execution guidance for the renamed or added queue/evaluation files.
- [x] 6.4 Regenerate saved synthetic outputs and execute the notebook sequence cleanly so committed notebook outputs are coherent.

## 7. Verification

- [x] 7.1 Run the full test suite with `uv run pytest`.
- [x] 7.2 Run the pipeline with output writing enabled and verify all documented CSV outputs are produced.
- [x] 7.3 Run notebook execution verification for all business-facing notebooks and confirm no traceback outputs or stale execution-order artifacts remain.
