## Context

The active employee-pay-cycle notebook currently satisfies a broad reporting contract by placing scenario sanity checks, benchmark summaries, and raw diagnostic tables directly in the main narrative. That makes the rendered report useful for audit, but less effective as a decision narrative for readers who primarily need to understand the residual-review problem, model tradeoffs, and final recommendation.

The source of truth remains the Jupytext percent-format notebook at `notebooks/snf_payroll_ranker_report.py`. The existing scenario benchmark, evaluation outputs, scoring outputs, and appendix diagnostics remain valid runtime artifacts. This change narrows the presentation contract rather than changing data generation, model scoring, or benchmark computation.

## Goals / Non-Goals

**Goals:**

- Make the main notebook narrative decision-focused from top to bottom.
- Allow simulation sanity evidence to be summarized as a short stress-design bridge rather than a table-heavy standalone main section.
- Prefer reader-facing plots, cards, and compact examples in the main narrative.
- Preserve detailed scenario catalogs, metric tables, data dictionaries, calibration diagnostics, and audit examples in the technical appendix.
- Keep all evidence based on active employee-cycle runtime artifacts.

**Non-Goals:**

- Change generated synthetic payroll data, labels, or anomaly scenario definitions.
- Change model training, scoring, evaluation metrics, or scenario benchmark aggregation logic.
- Add dependencies or new public Python APIs.
- Remove audit evidence from the notebook entirely.

## Decisions

- **Decision: Treat main narrative outputs as decision support, not audit export.** Main sections should use one or two high-signal visuals or cards per topic, with raw frames retained only when they directly answer a reader decision question. Alternative considered: keep all required tables in main sections and add plots around them. That keeps audit coverage but does not solve the narrative-density problem.

- **Decision: Move detailed sanity evidence to the appendix while preserving a compact stress-design explanation in the main narrative.** The main narrative should still explain that scenarios vary residual issue density, severity, dollars, issue mix, and label bias, but detailed cross-scenario rows do not need to interrupt the decision flow. Alternative considered: delete sanity evidence entirely. That would weaken trust in the synthetic benchmark and make the report harder to audit.

- **Decision: Keep scenario benchmark computation unchanged and alter only presentation.** Winner-frequency tables, median metric summaries, and winner-map rows remain available from the benchmark result object. Notebook code may render those artifacts as plot-first summaries in the main narrative and detailed tables in the appendix. Alternative considered: add new benchmark result types or plotting helpers in `src/`. That is unnecessary because the change is presentation-scoped.

- **Decision: Maintain appendix completeness.** Synthetic-data transparency, schema dictionaries, hard-rule definitions, metric definitions, scenario catalogs, benchmark tables, calibration diagnostics, and examples should remain accessible after the main narrative. Alternative considered: shorten the entire notebook by removing diagnostics. That would conflict with reproducibility and audit needs.

## Risks / Trade-offs

- **Risk: Moving tables out of the main narrative may make methodology details less visible.** Mitigation: include short bridge prose and link-style wording that names the appendix support artifacts.
- **Risk: Plot-first summaries may hide exact benchmark values.** Mitigation: retain detailed metric and winner tables in appendix or compact support cells.
- **Risk: A more flexible section contract may reduce consistency across report versions.** Mitigation: keep the high-level decision flow fixed even if section 4 is merged, shortened, or reframed.
- **Risk: Notebook validation may catch Lets-Plot rendering issues after presentation edits.** Mitigation: run `uv run prek run --all-files`, reduced Jupytext execution validation, smoke tests, and notebook/plotting regression tests.
