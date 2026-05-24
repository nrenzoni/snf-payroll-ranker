## Context

The current repository documents and implements a shift-level SNF approval workflow built around hybrid scoring and business-facing value proof notebooks. That direction no longer matches the intended product shape: the active system should be an employee-pay-cycle payroll ranking library whose first phase compares formulations, validates failure modes, and promotes only production-candidate components. The older shift-level hybrid path still contains useful ideas and should remain available for traceability, but it should stop defining active requirements or package boundaries.

## Goals / Non-Goals

**Goals:**
- Establish employee-pay-cycle as the only canonical active modeling grain.
- Separate active runtime/research direction from deprecated historical reference material in specs and top-level docs.
- Define a clean migration path where reusable code is kept or ported, while wrong-grain code is moved under an explicitly deprecated boundary.
- Preserve enough historical documentation to recover ideas without presenting legacy behavior as current contract.

**Non-Goals:**
- Implement the new employee-pay-cycle runtime in this change.
- Delete all shift-level code immediately.
- Finalize the exact production model family, dependency stack, or benchmark results.

## Decisions

### Active direction is employee-pay-cycle only
The active project contract will treat employee-pay-cycle as the primary payroll record grain for synthetic data, scoring, evaluation, and queue generation.

Alternatives considered:
- Keep both shift-level and employee-pay-cycle active: rejected because dual active grains would continue to blur contracts and prolong the incorrect original framing.
- Preserve shift-level as the documented baseline: rejected because the user explicitly does not want legacy code to remain part of active runtime, production, or research evaluation.

### Phase 1 is production-oriented research, not benchmark-only work
The library will be described as a production-oriented payroll ranking system whose Phase 1 validates formulations before promotion into operational use.

Alternatives considered:
- Describe the project as benchmark-first only: rejected because the intended end state is reusable production library code, not a standalone research artifact.
- Keep business proof as the dominant story: rejected because it incorrectly centers the deprecated shift-level hybrid workflow.

### Legacy shift-level hybrid work remains as deprecated reference only
Legacy shift-level scoring, notebooks, and business-proof narratives will remain in the repository for traceability, but they will be documented as non-normative and excluded from active runtime, research, and production paths.

Alternatives considered:
- Delete legacy artifacts entirely: rejected because useful implementation ideas may still need to be recovered.
- Leave legacy artifacts in place without explicit status: rejected because that would continue to confuse active requirements.

### Deprecation boundary should become structural, not only narrative
The long-term package boundary will isolate deprecated code under an explicitly marked deprecated or legacy namespace and remove active-runtime imports from that area.

Alternatives considered:
- Documentation-only deprecation: rejected because runtime coupling would remain easy to reintroduce.
- Immediate full move out of `src/`: deferred because some code may first need to be ported into the new employee-pay-cycle path.

## Risks / Trade-offs

- [Spec/doc reset gets ahead of runtime changes] → Mitigation: mark the change as a directional and contract correction, then follow with implementation changes that align code to the new active specs.
- [Legacy and active terminology coexist for a while] → Mitigation: consistently label shift-level hybrid material as deprecated historical reference in README, architecture, ADRs, and spec deltas.
- [Useful shift-level logic becomes harder to discover after isolation] → Mitigation: keep legacy reference code and notebooks documented, searchable, and clearly named rather than deleting them.
- [The employee-pay-cycle direction still needs detailed runtime design] → Mitigation: keep this design focused on project boundaries and require follow-on implementation changes for model APIs, data contracts, and evaluation pipelines.
