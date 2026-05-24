## 1. Direction Reset

- [x] 1.1 Update active runtime-facing docs to make employee-pay-cycle the canonical modeling grain
- [x] 1.2 Add an ADR or decision-log entry that explicitly supersedes the older shift-level primary-grain decision
- [x] 1.3 Update research log and architecture notes to describe Phase 1 as production-oriented research and demote the hybrid shift-level path to legacy reference only

## 2. Legacy Boundary

- [ ] 2.1 Inventory existing shift-level modules, notebooks, and docs for reuse, porting, or deprecation
- [ ] 2.2 Move or rename non-reused shift-level runtime code into an explicitly deprecated or legacy reference boundary
- [ ] 2.3 Remove active-runtime imports and acceptance criteria that depend on deprecated shift-level hybrid code

## 3. Employee-Pay-Cycle Runtime Follow-Up

- [x] 3.1 Define active employee-pay-cycle synthetic data contracts and result objects
- [x] 3.2 Rebuild active scoring interfaces around employee-pay-cycle formulation comparison rather than a single hybrid score
- [ ] 3.3 Rebuild active evaluation and queue contracts around employee-pay-cycle grouped ranking and production-candidacy reporting

## 4. Verification

- [x] 4.1 Run `uv run prek run --all-files` after runtime and notebook changes
- [x] 4.2 Run targeted `uv run pytest` coverage for changed runtime behavior once the employee-pay-cycle path is implemented
