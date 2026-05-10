## Context

Notebook sources are maintained as Jupytext `.py` files, while paired `.ipynb` files are generated artifacts that should only be refreshed intentionally. The project already has a `NOTEBOOK_FAST=1` execution convention for internal diagnostic notebooks, but the contributor workflow does not yet make fast validation mandatory after notebook source edits.

Recent SNF notebook work added or changed notebooks that execute meaningful pipeline code. Some notebook failures were not caught because the implementation cycle relied on normal tests and `prek`, neither of which executes every changed notebook cell. The fix is a workflow and notebook-support change, not a new runtime API.

## Goals / Non-Goals

**Goals:**

- Make fast notebook execution the required validation path after changing notebook `.py` sources.
- Keep fast validation non-destructive by writing executed notebooks to `/tmp` instead of updating paired `.ipynb` artifacts.
- Clarify when full non-fast execution is appropriate: explicit rerender, paired output refresh, analyst-visible output synchronization, or full-workload validation.
- Add fast-mode support to notebooks that run material pipeline workloads and would otherwise make routine validation slow or incomplete.

**Non-Goals:**

- Do not replace full notebook rerendering when refreshed paired `.ipynb` outputs are requested.
- Do not introduce new notebook dependencies or change the Jupytext pairing format.
- Do not require every lightweight notebook to reduce its workload if the standard fast command already executes it quickly and safely.
- Do not change pipeline output semantics or public result object contracts.

## Decisions

- Use the existing `NOTEBOOK_FAST=1` environment switch rather than adding a new CLI flag or config file. This preserves the current Jupytext command shape and keeps notebook-local fast behavior explicit.
- Use `--to ipynb --execute --run-path notebooks --output /tmp/<notebook>.fast.ipynb` for routine notebook validation. This verifies cell execution while avoiding accidental paired `.ipynb` diffs.
- Reserve `uv run jupytext --set-formats ipynb,py:percent --execute <notebook.py>` for full rerenders and explicitly requested output synchronization. This keeps intentional artifact refreshes separate from routine error checks.
- For notebooks that call `run_pipeline()` several times or generate heavier diagnostics, use existing pipeline artifact selection where possible, such as `PipelineIncludeConfig.scored_only()` in fast mode. If a notebook displays outputs that require additional artifacts, choose the smallest include configuration that supports those cells.
- Document the workflow in `AGENTS.md` so future AI development cycles run notebook execution checks whenever notebook sources change.

## Risks / Trade-offs

- Fast mode could skip a failure that appears only in full dense execution -> Mitigate by requiring full non-fast execution when the user requests a rerender, paired output refresh, analyst-visible output sync, or full-workload validation.
- A notebook may use outputs not available from `scored_only()` -> Mitigate by selecting the smallest sufficient pipeline include configuration per notebook rather than assuming every notebook can be scored-only.
- Running fast notebook checks after every notebook change adds development time -> Mitigate by using reduced workloads and `/tmp` outputs so validation remains practical and avoids noisy artifact diffs.
- Documentation-only guidance can be missed by future agents -> Mitigate by placing the requirement in both the OpenSpec capability and `AGENTS.md` verification workflow.
