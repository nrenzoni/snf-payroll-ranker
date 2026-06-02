# Research Log

## Employee-Pay-Cycle Active Direction

- This section supersedes the earlier shift-level primary-grain assumption below.
- Employee-pay-cycle is the active modeling grain for future runtime, evaluation, and production-promotion work.
- Phase 1 is production-oriented research: compare formulations, validate failure modes, and only promote methods or library components that earn production candidacy.
- Lower-level shift, schedule, and timeclock information may still be generated or engineered as supporting context, but they are no longer the canonical active row contract.
- The active notebook benchmark is now framed around `DGP scenario x seed x model x review budget x metric` rather than a single synthetic run.
- The interim notebook default keeps the scenario benchmark at one seed for runtime control, but the benchmark helpers are intentionally multi-seed capable for expanded post-run sweeps.
- Benchmark interpretation distinguishes random-draw stability within a DGP from structural robustness across DGP scenarios; one seed does not resolve structural DGP bias.

## SNF Shift-Level Payroll Domain Assumptions

- Deprecated historical assumptions retained for traceability only.
- The synthetic world represents a multi-facility skilled nursing facility operator where weekly payroll approval is performed by administrator-facing teams rather than a dedicated forensic payroll analyst team.
- Shift-level records are the modeling grain because overtime, double shifts, rest gaps, weekend/shift differentials, and schedule/timeclock mismatches require shift context that employee-pay-period aggregates hide.
- Initial implemented scenarios focus on the two highest-value administrator approval workflows: overtime/double-shift staffing pressure and premium pay or shift differential mismatch.
- Agency/float labor, census/acuity, credential/license mismatch, PBJ category mismatch, meal premiums, lifecycle, retro/rate corrections, union policies, new-client bootstrap, and payroll close adjustment concentration are documented as future scenario families.
- Synthetic pay policy defaults are illustrative only and are not legal, payroll, union-contract, or state-specific compliance guidance.
- Transferable features should prefer stationary ratios and facility-normalized references over raw dollar or raw hour thresholds so future client facilities with different rates, size, and staffing patterns can be bootstrapped more safely.
