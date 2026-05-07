## ADDED Requirements

### Requirement: Rich internal diagnostic notebooks with bounded defaults
The internal diagnostic notebooks SHALL use richer scenario sets that produce informative data-science plots while remaining reproducible with bounded local execution defaults.

#### Scenario: Internal statistical notebook uses richer comparison units
- **WHEN** `notebooks/06_internal_statistical_diagnostics.py` runs with default settings
- **THEN** it evaluates diagnostics across multiple scenarios, seeds, or temporal origins and renders component superiority, subgroup, calibration, robustness, and perturbation plots with visible contrast or interpretable uncertainty

#### Scenario: Internal simulation notebook uses scenario-dependent queue stress
- **WHEN** `notebooks/07_simulation_and_stress_testing.py` runs with default settings
- **THEN** it renders queue simulation and stress-test plots that show scenario-dependent differences in demand, overload, dollar capture, or missed exposure

#### Scenario: Fast mode is documented
- **WHEN** a user reviews the README or internal notebook setup cells
- **THEN** the documentation identifies bounded default scenario/seed/sample counts and explains which constants to reduce for faster local execution

#### Scenario: Business-facing notebooks remain independent
- **WHEN** internal diagnostic notebooks are updated
- **THEN** notebooks `01` through `05` remain available as the business-facing sequence and are not required to render the full internal scenario suite
