## 1. Pipeline Artifact Selection API

- [ ] 1.1 Add `PipelineIncludeConfig` to `src/payroll_anomaly_ranking/pipeline.py` with full-default behavior and a `scored_only()` named constructor.
- [ ] 1.2 Add `PipelineArtifactNotGeneratedError` with an actionable message for excluded artifact access.
- [ ] 1.3 Refactor `PipelineResults` so always-generated artifacts remain direct fields and conditionally generated artifacts are private optional fields exposed through properties.
- [ ] 1.4 Update `run_pipeline` to accept the include configuration and skip validation outputs, aggregations, evaluation, backtests, rolling-origin outputs, review queues, and leakage checks when excluded.
- [ ] 1.5 Ensure `write_pipeline_outputs` only writes artifacts that were generated, or fails with the custom exception when required output artifacts are excluded.

## 2. Fast Notebook Integration

- [ ] 2.1 Update internal diagnostic notebook setup to choose full or scored-only pipeline include configuration based on `notebook_fast_mode()`.
- [ ] 2.2 Update notebook `06` direct `run_pipeline` calls that only consume `.scored` to pass scored-only include configuration in fast mode.
- [ ] 2.3 Update notebook `07` direct `run_pipeline` calls that only consume `.scored` to pass scored-only include configuration in fast mode.
- [ ] 2.4 Update `run_diagnostic_comparison_units` to accept or internally use scored-only pipeline execution when only scored rows are required.
- [ ] 2.5 Update `compare_scenarios` to use scored-only pipeline execution because queue simulation only consumes scored rows.

## 3. Documentation And Specs

- [ ] 3.1 Update `AGENTS.md` to document that fast notebook checks use reduced workloads, scored-only pipeline artifacts, and `/tmp` Jupytext output.
- [ ] 3.2 Update `README.md` engineering-facing notebook instructions to distinguish scored-only fast checks from full paired-output refreshes.
- [ ] 3.3 Add a brief research note to `RESEARCH_LOG.md` if implementation measurements or benchmark findings influence additional speed decisions.

## 4. Tests And Verification

- [ ] 4.1 Add tests that default `run_pipeline` still exposes all full artifacts.
- [ ] 4.2 Add tests that scored-only `run_pipeline` exposes payroll, labels, scored rows, and scenario metadata.
- [ ] 4.3 Add tests that accessing excluded scored-only artifacts raises `PipelineArtifactNotGeneratedError` instead of returning empty DataFrames.
- [ ] 4.4 Update notebook reproducibility/source tests to assert FAST_PATH uses the shared fast-mode helper and scored-only pipeline include configuration.
- [ ] 4.5 Run targeted pipeline/notebook tests, including `uv run pytest tests/integration/test_regression.py -k "notebook or plotting"` and relevant pipeline tests.
- [ ] 4.6 Run `uv run pytest tests/smoke`.
- [ ] 4.7 Run fast Jupytext checks for notebooks `06` and `07` with `NOTEBOOK_FAST=1`, `--run-path notebooks`, and `/tmp/...fast.ipynb` outputs.
- [ ] 4.8 Run `uv run prek run --all-files` and resolve all failures.
