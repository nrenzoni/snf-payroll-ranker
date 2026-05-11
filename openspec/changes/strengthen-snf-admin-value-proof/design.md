## Context

The current business-facing SNF notebook is optimized around queue walkthroughs and case examples, while the more rigorous method-comparison evidence lives in the technical notebook. That split leaves a gap for facility administrators who are sophisticated enough to challenge whether the hybrid ranking advantage is repeated, fair, and operationally meaningful, but who still need the notebook to stay business-readable and explanation-heavy.

The current threshold baseline implementation also has two limitations relative to that audience. First, the threshold family is incomplete because `facility payroll variance threshold` exists in spec/config but is not implemented in scoring or evaluation. Second, the notebook mostly compares fixed absolute thresholds, which are operationally plausible defaults but not a strong business-proof baseline for scenario-scaled synthetic payroll worlds. A stronger comparison needs a calibrated manual threshold pack that uses only administrator-style raw threshold fields, calibrates without labels, and remains visibly distinct from model-based ranking.

This change crosses scoring, evaluation, diagnostics, and notebook narrative. It also changes the intended role of notebook `08`, so the design needs to keep the technical method ladder explicit while preserving business-safe language and one concrete output example.

## Goals / Non-Goals

**Goals:**
- Implement the missing facility payroll variance threshold flag and include it in threshold baseline evaluation outputs.
- Add a calibrated combined manual threshold baseline that is realistic for each evaluated scenario world, uses only raw threshold fields, and remains label-free during calibration.
- Rework notebook `08` so the main body proves value across repeated scenario and seed worlds for facility-admin review decisions.
- Keep the notebook explanation-heavy, with clear plain-language sections on what thresholds, rules, robust statistics, ML, and hybrid ranking do and where each approach breaks down.
- Reduce dashboard-style clutter in the notebook main flow by keeping one concrete final ranked-output table and moving stress-oriented evidence into an appendix section.

**Non-Goals:**
- Replace or weaken notebook `09` as the technical ablation notebook.
- Introduce new external dependencies, dashboard infrastructure, or interactive controls.
- Redefine the full synthetic data generator around many new scenario families in this change.
- Turn manual thresholds into a learned ranking model; the manual baseline remains a threshold-driven comparator.

## Decisions

### 1. Add facility payroll variance as a first-class threshold flag in scoring

The scoring stage will emit a real `ScoreCol.THRESHOLD_FACILITY_VARIANCE_FLAG` so evaluation and notebook comparisons can treat it like the other administrator-style threshold baselines.

Rationale:
- The current spec surface already expects this threshold, so implementing it closes an existing behavior gap instead of inventing a new comparison.
- Keeping the flag in scoring preserves the current architecture where threshold baseline columns are generated alongside other score-related columns and then consumed by evaluation/notebooks.

Alternatives considered:
- Compute the facility variance baseline only inside the notebook. Rejected because it would create notebook-only behavior that is harder to test and inconsistent with the existing threshold baseline pipeline.
- Remove the facility variance requirement from spec. Rejected because the user explicitly wants it added now and the current spec already depends on it.

### 2. Introduce a calibrated manual threshold pack as the primary business-facing manual comparator

Evaluation will add a combined manual baseline that is constructed from the threshold-family raw fields only: gross pay, total hours, overtime hours, premium dollars, paid-vs-scheduled variance, and facility payroll variance. The threshold pack will calibrate cutoffs from reference periods in the scored dataset without using labels, anomaly dollars, or model scores. The resulting cutoffs will then be frozen and evaluated on later periods or the evaluation slice used by the notebook.

Rationale:
- This gives the business notebook a realistic threshold comparator that reflects how a competent administrator team would tune review cutoffs to observed payroll context instead of relying on arbitrary global constants.
- It keeps the manual baseline honest by using only raw operational fields and threshold logic instead of learned ranking.
- It is harder to dismiss than individual fixed thresholds alone, while the individual threshold outputs can still remain available as diagnostic evidence.

Alternatives considered:
- Keep only individual fixed thresholds. Rejected because that remains too easy to challenge as unrealistic or weak in scenario-scaled worlds.
- Convert the manual baseline to a weighted threshold score or learned logistic blend. Rejected because that would blur the line between manual threshold review and model-based ranking.
- Calibrate thresholds with labels or synthetic dollar targets. Rejected because that would undermine the “manual baseline” framing and create leakage concerns.

### 3. Keep repeated-world proof in the business notebook, but separate comparator types

Notebook `08` will explicitly separate two comparison frames. Thresholds and the calibrated manual threshold pack will be compared on burden, missed risk, and value capture because thresholds have native variable review volume. Rule-only, statistics-only, ML-only, and hybrid ranking will be compared at fixed facility review budgets because they are rankable methods.

Rationale:
- This is the fairest comparison structure for a skeptical facility-admin audience.
- It avoids pretending that a binary threshold is the same kind of object as a ranked queue.
- It preserves the user’s requirement that the notebook be rigorous and not hinge on a single hand-picked plot.

Alternatives considered:
- Force every baseline into a top-K comparison. Rejected because binary threshold baselines do not naturally operate that way.
- Compare everything only at native review volume. Rejected because it obscures the ranking value of hybrid, rules, statistics, and ML under constrained capacity.

### 4. Re-center notebook `08` on repeated scenario-by-seed proof and move stress evidence into an appendix

The main body of `08` will use repeated runs across `baseline`, `overtime-staffing-pressure`, and `premium-mismatch`. Stress evidence will move into an appendix section and should use true stress constructions or true queue-stress diagnostics rather than presenting existing alias presets as distinct stress worlds.

Rationale:
- The main body stays readable and business-focused while still showing repeated evidence.
- The appendix can answer deeper skepticism without overwhelming the primary story.
- This avoids overstating the significance of current alias presets that are mainly renamed scenario families with different seeds.

Alternatives considered:
- Put all drift and stress variants in the main flow. Rejected because it would overload the business notebook and dilute the primary narrative.
- Reuse alias presets without comment. Rejected because that is weaker evidence than the user wants and risks a misleading proof claim.

### 5. Keep one concrete ranked-output table and use narrative around every major visual

The notebook will present one final ranked-output table with review-safe fields. Earlier notebook sections will prefer plots and short explanatory markdown blocks over repeated DataFrame dumps.

Rationale:
- Facility admins need to see what the output looks like, but too many tables pull the notebook back toward a dashboard.
- Explicit narrative around each method and each visual reduces confusion and aligns with the user’s preference for more explanation, not less.

Alternatives considered:
- Keep the existing queue tables and case cards in the main flow. Rejected because they consume attention without doing the repeated-proof work.

## Risks / Trade-offs

- `[Scenario-calibrated thresholds look too favorable to manual baselines]` → Keep calibration label-free, explain the calibration window explicitly, and preserve individual threshold diagnostics so reviewers can still see overflagging and blind spots.
- `[Facility-admin business notebook becomes too technical]` → Use plain-language markdown before and after each major figure and reserve deeper stress diagnostics for the appendix.
- `[True stress appendix requires more implementation than alias-based appendix]` → Scope appendix evidence to supported diagnostics first, such as queue-capacity stress and true drift helpers where already supported, and add narrowly targeted scenario extensions only where necessary.
- `[New threshold columns and evaluation outputs complicate notebook code]` → Keep threshold data in Polars DataFrames with explicit schema columns and add small typed helper/result objects only when multiple related outputs must travel together.
- `[Changing comparison units exposes existing assumptions about pay-period-only review budgets]` → Document whether the notebook uses facility-level review framing, and keep the implementation aligned with the facility-admin audience rather than preserving a less relevant global assumption.

## Migration Plan

1. Add facility payroll variance threshold scoring and wire it into threshold baseline evaluation outputs.
2. Add calibrated manual threshold pack evaluation helpers and repeated-world comparison helpers needed by notebook `08`.
3. Update specs to reflect the business-proof notebook role, calibrated manual baseline, and appendix stress framing.
4. Rewrite notebook `08` to use the new proof structure and explanatory narrative.
5. Validate with notebook fast execution, `uv run prek run --all-files`, and targeted tests for scoring/evaluation behavior.

No external migration or rollback plan is required because the change is internal to the project’s scoring, evaluation, and notebook artifacts. If needed, the notebook can temporarily continue to use the old threshold comparison helpers while the new calibrated baseline is being implemented, but the final change should remove that split behavior.

## Open Questions

- Should the calibrated manual threshold pack target a fixed review-rate band per facility-period, or should it optimize a simpler unsupervised calibration objective such as upper-quantile cutoffs on each raw threshold field?
- Should facility-admin business-proof comparisons switch all ranking comparisons to facility-by-pay-period budgets, or should the notebook retain existing pay-period budgets with explicit facility summary framing?
- Which appendix stress views should be implemented first if time is constrained: queue-capacity stress, subgroup drift, or calendar drift?
