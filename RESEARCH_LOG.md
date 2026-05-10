# Research Log

## SNF Shift-Level Payroll Domain Assumptions

- The synthetic world represents a multi-facility skilled nursing facility operator where weekly payroll approval is performed by administrator-facing teams rather than a dedicated forensic payroll analyst team.
- Shift-level records are the modeling grain because overtime, double shifts, rest gaps, weekend/shift differentials, and schedule/timeclock mismatches require shift context that employee-pay-period aggregates hide.
- Initial implemented scenarios focus on the two highest-value administrator approval workflows: overtime/double-shift staffing pressure and premium pay or shift differential mismatch.
- Agency/float labor, census/acuity, credential/license mismatch, PBJ category mismatch, meal premiums, lifecycle, retro/rate corrections, union policies, new-client bootstrap, and payroll close adjustment concentration are documented as future scenario families.
- Synthetic pay policy defaults are illustrative only and are not legal, payroll, union-contract, or state-specific compliance guidance.
- Transferable features should prefer stationary ratios and facility-normalized references over raw dollar or raw hour thresholds so future client facilities with different rates, size, and staffing patterns can be bootstrapped more safely.
