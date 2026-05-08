## Why

Fast Jupytext notebook checks now reduce notebook-level workloads, but they still trigger full pipeline artifact generation when a notebook only needs scored payroll rows. This makes FAST_PATH execution slower than necessary and creates an unclear contract for consumers that intentionally skip expensive artifacts.

## What Changes

- Add an explicit pipeline include configuration for selecting which runtime artifacts `run_pipeline` generates.
- Keep full artifact generation as the default behavior for existing callers and full notebook refreshes.
- Add a scored-only include profile for fast notebook execution paths that need generated/scored rows but not evaluation tables, queues, backtests, or rolling-origin outputs.
- Make excluded artifact access fail loudly with a custom exception rather than returning placeholder empty `pl.DataFrame` objects.
- Update internal notebook fast paths and diagnostic helpers to use scored-only pipeline execution where they only consume `.scored`.
- Update engineering-facing documentation and tests to distinguish full artifact refresh from fast scored-only execution checks.

## Capabilities

### New Capabilities
- `pipeline-artifact-selection`: Selective pipeline artifact generation and explicit access semantics for artifacts that were not generated.

### Modified Capabilities
- `notebook-reproducibility`: Fast notebook execution checks use reduced diagnostic workloads and scored-only pipeline artifacts while full notebook refreshes continue to generate paired outputs and full artifacts.

## Impact

- Affected code: `src/payroll_anomaly_ranking/pipeline.py`, notebook diagnostic helpers, queue simulation helpers, and internal notebooks `06` and `07`.
- API impact: `run_pipeline` gains an include configuration parameter with default full behavior; `PipelineResults` conditionally generated artifacts become property-backed and raise a custom exception when accessed without being generated.
- Documentation impact: engineering-facing notebook execution instructions describe scored-only FAST_PATH behavior and full paired-output refresh behavior.
- Verification impact: targeted pipeline/notebook tests should cover default full behavior, scored-only behavior, exception semantics, fast Jupytext execution to `/tmp`, smoke tests, and `uv run prek run --all-files`.
