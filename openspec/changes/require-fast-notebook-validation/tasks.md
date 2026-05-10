## 1. Notebook Fast-Mode Support

- [x] 1.1 Identify changed or recently added notebooks that perform material pipeline work and lack `NOTEBOOK_FAST` handling.
- [x] 1.2 Add fast-mode handling to the SNF case-study notebook using `notebook_fast_mode()` and the smallest sufficient `PipelineIncludeConfig` for displayed cells.
- [x] 1.3 Confirm fast-mode notebook execution still produces the result objects and tables used by the affected notebook cells.

## 2. Workflow Documentation

- [x] 2.1 Update `AGENTS.md` to require fast Jupytext validation after any notebook `.py` source change.
- [x] 2.2 Clarify in `AGENTS.md` that full non-fast Jupytext execution is only for requested rerenders, paired `.ipynb` refreshes, analyst-visible output sync, or full-workload validation.

## 3. Verification

- [x] 3.1 Run the fast Jupytext validation command for each notebook changed during implementation, writing executed outputs only under `/tmp`.
- [x] 3.2 Run `uv run prek run --all-files` and resolve any reported issues.
- [x] 3.3 Run `uv run pytest tests/integration/test_regression.py -k "notebook or plotting"` if notebook contract behavior changes beyond documentation.
