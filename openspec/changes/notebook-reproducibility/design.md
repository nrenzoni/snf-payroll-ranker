## Context

The internal diagnostic notebooks now have a `NOTEBOOK_FAST=1` execution path that reduces notebook-level scenario counts, seeds, and Monte Carlo iterations. The current notebooks and diagnostic helper functions still call `run_pipeline`, which always generates every pipeline artifact: validation summaries, aggregations, evaluation tables, backtests, rolling-origin outputs, review queues, leakage checks, and scored rows. Fast notebook checks usually only need `.scored`, so full artifact generation adds avoidable runtime.

`PipelineResults` currently exposes all artifacts as required dataclass fields. If `run_pipeline` becomes selective, consumers need explicit access semantics so excluded artifacts cannot be confused with legitimate empty results.

## Goals / Non-Goals

**Goals:**

- Preserve existing full `run_pipeline` behavior by default.
- Add a typed include configuration for selecting generated pipeline artifact groups.
- Provide a scored-only include profile for fast notebook diagnostics and helper functions that only consume scored rows.
- Make access to excluded artifacts raise a custom, actionable exception.
- Keep full notebook refreshes and analyst-visible outputs on the default full artifact path.

**Non-Goals:**

- Do not add persistent caches for notebook outputs or pipeline intermediates.
- Do not reduce model fidelity for full notebook refreshes.
- Do not introduce Papermill or another notebook executor.
- Do not add compatibility shims for mapping-style result access or tuple unpacking.

## Decisions

### Add `PipelineIncludeConfig`

`run_pipeline` will accept an include configuration with full generation as the default. The configuration will group artifacts by pipeline stage rather than exposing one flag per result field where a group naturally shares work.

The include config should provide named constructors such as `all()` and `scored_only()`. `scored_only()` will disable validation outputs, aggregations, evaluation, backtests, rolling-origin metrics, review queues, and leakage checks while preserving generated payroll, labels, scored rows, and scenario metadata.

Alternative considered: add a separate `run_scoring_pipeline` function. This would be smaller but creates a second canonical pipeline entry point and makes future stage sharing more awkward. A single selective `run_pipeline` keeps the API centered on one orchestration path.

### Use property-backed optional artifacts

`PipelineResults` will keep always-generated artifacts as required public fields and store conditionally generated artifacts in private optional fields. Public properties will return generated artifacts or raise `PipelineArtifactNotGeneratedError` with a message naming the missing artifact and include configuration remedy.

Alternative considered: return empty `pl.DataFrame()` for excluded artifacts. This was rejected because it can silently mask skipped work and is hard to distinguish from a valid empty result.

### Apply scored-only mode only to fast/internal paths

Notebook FAST_PATH setup and internal helpers that only need `.scored` will request `PipelineIncludeConfig.scored_only()`. Full notebook refresh commands and existing default callers will continue using all artifacts.

Alternative considered: use scored-only mode for all notebook execution. This was rejected because full analyst-visible notebook refreshes should exercise the complete artifact path when outputs are regenerated.

### Keep Jupytext artifact behavior separate from pipeline artifact selection

Jupytext fast execution will continue writing executed notebooks to `/tmp` with `--to ipynb --execute --run-path notebooks --output /tmp/...fast.ipynb`. Pipeline include selection only controls runtime objects produced inside Python.

## Risks / Trade-offs

- Existing code may instantiate `PipelineResults` directly in tests → Update tests to use the new private fields or prefer `run_pipeline` fixtures.
- Optional private fields add dataclass verbosity → Keep property helper logic centralized in `PipelineResults`.
- Some skipped artifacts may share expensive prerequisites with requested artifacts → Group include flags by work stage and keep core scoring prerequisites always explicit.
- FAST_PATH may still be slow because scoring itself runs Isolation Forest and uncertainty logic → Measure after scored-only changes before considering model-fidelity reductions.
- Consumers may accidentally request scored-only and then access full artifacts → Custom exception makes the failure immediate and actionable.
