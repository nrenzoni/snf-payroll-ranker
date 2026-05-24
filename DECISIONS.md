# Decision Log

This log records significant technical decisions made during the design and evolution of the SNF Payroll Anomaly Ranking pipeline. Each entry follows the context / decision / consequences structure.

---

## ADR-006: Employee-Pay-Cycle Supersedes Shift-Level As The Active Grain

**Context**
The repository was previously framed around shift-level SNF approval scoring. That framing is no longer the intended product direction. The active project needs a single canonical modeling object for runtime-library work, research evaluation, and later production promotion.

**Decision**
Use employee-pay-cycle as the active modeling grain. Lower-level shift, schedule, and timeclock data may remain as optional supporting context, but they no longer define the active runtime contract.

**Consequences**
- Positive: Aligns the active runtime with the intended payroll ranking object and avoids a split identity between shift-level and employee-cycle work.
- Positive: Simplifies future model, metric, and queue contracts by giving the project one canonical scoring grain.
- Negative: Existing shift-level code, notebooks, and specs become deprecated historical reference and must be isolated or ported carefully.
- Negative: Some lower-level signal engineering will need to be reintroduced as supporting context rather than as the primary row contract.

---

## ADR-007: Production-Oriented Research Is The Active Phase-1 Contract

**Context**
The earlier repository story centered a hybrid SNF business-proof workflow. The intended end state is broader: build reusable library code, validate competing formulations, and only promote methods that are strong enough for later production use.

**Decision**
Describe the active project as a production-oriented payroll ranking library whose Phase 1 is comparative research and validation. Deprecated shift-level hybrid workflow code remains only as historical reference and is not part of the active runtime, research, or production path.

**Consequences**
- Positive: The project can evaluate formulations rigorously without claiming that a legacy hybrid workflow is already the chosen production architecture.
- Positive: Documentation, specs, and future runtime changes can clearly separate active and deprecated paths.
- Negative: Existing business-facing notebook narratives must be relabeled or isolated as legacy material.
- Negative: Contributors need to avoid reintroducing dependencies on deprecated shift-level code during migration.

---

## ADR-001: Polars as the Primary DataFrame Engine

**Context**
The pipeline processes tens of thousands of shift-level records per pay period with many rolling, grouped, and joined operations. pandas performance and memory usage were acceptable for prototyping but became a friction point when iterating on feature engineering and temporal evaluation.

**Decision**
Use Polars for all tabular operations. pandas is not used anywhere in the runtime or notebooks.

**Consequences**
- Positive: Significant speedup in grouped aggregations, rolling windows, and joins. Lower memory footprint during temporal cross-validation.
- Positive: Native expression API encourages vectorized, declarative transforms rather than row-wise Python callbacks.
- Negative: Smaller ecosystem of Stack Overflow answers and third-party integrations; team must be comfortable reading Polars documentation.
- Negative: Some pandas-centric libraries (e.g., certain plotting helpers) require conversion or are avoided.

---

## ADR-002: Shift-Level Modeling Grain

**Status**
Superseded by ADR-006.

**Context**
Payroll anomaly detection can be framed at the employee-pay-period aggregate (one row per employee per pay period) or at the shift level (one row per shift). Aggregate views are simpler but hide overtime patterns, double-shift sequences, rest gaps, and shift-specific premium mismatches.

**Decision**
Model at the shift level. All features, rules, scores, and evaluation metrics are computed per shift. Pay-period/facility summaries are rolled up from shift-level results.

**Consequences**
- Positive: Overtime, double-shift, rest-gap, schedule/timeclock mismatch, and premium eligibility can be detected with shift context.
- Positive: Facility approval summaries remain traceable to underlying shift details.
- Negative: Higher row count and more complex temporal grouping for peer baselines.
- Negative: Requires careful handling of shift date boundaries and pay period mapping.

---

## ADR-003: Fully Synthetic Data for Privacy and Reproducibility

**Context**
The project is intended as a public portfolio piece and teaching artifact. Using any real payroll data would introduce legal risk, require de-identification auditing, and make the repository non-reproducible for external reviewers.

**Decision**
Generate all data synthetically from code. No real employee identifiers, resident data, payroll records, tax records, bank details, HR comments, or production integrations are included. Synthetic labels are injected for evaluation but are never used as model features.

**Consequences**
- Positive: Repository is fully reproducible from a clean checkout. Anyone can run the pipeline and get identical outputs.
- Positive: Zero privacy review or legal clearance required for public sharing.
- Positive: Scenario control (drift, anomaly concentration, calendar effects) is possible via configurable scenario specs.
- Negative: Synthetic distributions are simpler than real SNF payroll operations; generalization claims must be carefully scoped.
- Negative: Some real-world edge cases (union policy variation, state-specific compliance, agency billing) are documented but not yet implemented.

---

## ADR-004: Hybrid Scoring Over a Single End-to-End Model

**Status**
Superseded by ADR-007 for the active project direction. Retained as historical context for the deprecated shift-level workflow.

**Context**
A common approach in anomaly detection is to train a single unsupervised model and use its output score directly. For SNF payroll, this risks missing deterministic compliance issues or misinterpreting legitimate high-dollar shifts as anomalous.

**Decision**
Build a hybrid approval exception score that combines independent components: deterministic rules, robust statistics, unsupervised ML, peer context, employee history, schedule/timeclock mismatch, premium eligibility, and estimated exposure. Each component is computed independently and combined via configurable weights.

**Consequences**
- Positive: Inspectable. An administrator can see which components drove a record's ranking.
- Positive: Tunable. Facility operators can adjust weights to reflect local pay policy or review capacity.
- Positive: Resilient. If one component fails (e.g., peer group too small), others continue to contribute.
- Negative: More engineering effort than a single model endpoint.
- Negative: Requires careful normalization and clipping so components are comparable on a 0-1 scale.

---

## ADR-005: Jupytext-Paired Notebooks Over Raw .ipynb Artifacts

**Context**
Notebooks are the primary vehicle for business-facing case studies and data-science diagnostics. Raw `.ipynb` files are large JSON blobs that create noisy diffs, merge conflicts, and code-review friction.

**Decision**
Use Jupytext to pair `.ipynb` outputs with `.py` percent-format sources. The `.py` files are the source of truth. `.ipynb` artifacts are generated on demand and are not edited directly. Shared plotting adapters live in `notebooks/common/plots.py` to keep the runtime package free of Jupyter and plotting dependencies.

**Consequences**
- Positive: Git diffs are readable Python code. Code review in PRs is natural.
- Positive: Notebook logic can be linted, formatted, and type-checked alongside runtime code.
- Positive: Runtime package remains free of heavy notebook dependencies; `uv sync --extra notebooks` is optional.
- Negative: Reviewers must remember to regenerate paired `.ipynb` when executing the full workload.
- Negative: Some notebook-only UI state (collapsed cells, widget outputs) is lost in the `.py` source.

---
