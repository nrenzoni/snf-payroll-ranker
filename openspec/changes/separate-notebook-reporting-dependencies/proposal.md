## Why

The core package is intended for downstream payroll anomaly ranking pipelines, but it currently imports notebook-only plotting code and requires Jupyter/Lets-Plot dependencies at runtime. Separating notebook/reporting concerns from the pipeline package will make downstream installs smaller, clearer, and less likely to fail in non-notebook execution environments.

## What Changes

- Remove Lets-Plot chart helpers from the core `payroll_anomaly_ranking` package.
- Move one-off visual encodings into the Jupytext notebook sources, with any shared notebook-only presentation helpers living under `notebooks/` rather than `src/`.
- Split package dependencies so core runtime installs include only pipeline dependencies, while notebook/reporting tools are available through an optional extra or equivalent UV-supported optional dependency path.
- Update README, contributor guidance, and notebook reproducibility documentation to describe the package boundary and notebook setup command.
- Preserve existing notebook visual coverage and reproducibility expectations after the dependency split.

## Capabilities

### New Capabilities
- `runtime-dependency-boundary`: Defines the boundary between downstream pipeline runtime dependencies and optional notebook/reporting dependencies.

### Modified Capabilities
- `notebook-reproducibility`: Notebook execution requirements will explicitly use the notebook/reporting dependency environment while preserving clean execution and paired output refresh expectations.
- `payroll-review-queue`: Required business visuals continue to render from synthetic outputs, but chart construction becomes notebook/reporting code instead of core package code.

## Impact

- Affected package metadata: `pyproject.toml` dependency declarations and lockfile resolution.
- Affected core code: removal or relocation of `src/payroll_anomaly_ranking/charts.py` and any imports from it.
- Affected notebooks: plotting imports and chart cells in Jupytext `.py` sources under `notebooks/`.
- Affected docs/specs/tests: README setup instructions, `AGENTS.md`, notebook reproducibility specs, and tests that assert notebook plotting setup or chart availability.
- Downstream impact: pipeline consumers can install and run `payroll_anomaly_ranking` without Jupyter or Lets-Plot. Notebook users must install the notebook/reporting optional dependencies before executing notebooks.
