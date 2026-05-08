## ADDED Requirements

### Requirement: Core runtime excludes notebook reporting dependencies
The project SHALL define a core runtime environment for downstream payroll anomaly ranking pipelines that does not require Jupyter, Jupytext, nbconvert, or Lets-Plot packages.

#### Scenario: Pipeline installs without reporting tools
- **WHEN** a downstream pipeline installs the project core runtime dependencies
- **THEN** it can import and run the payroll anomaly ranking pipeline without installing Jupyter, Jupytext, nbconvert, or Lets-Plot

#### Scenario: Core package does not import plotting libraries
- **WHEN** modules under `src/payroll_anomaly_ranking` are imported by downstream pipeline code
- **THEN** those imports do not import Lets-Plot or Jupyter-only modules

### Requirement: Notebook reporting dependencies are explicit
The project SHALL provide a documented notebook/reporting dependency environment for executing Jupytext notebooks and rendering Lets-Plot visuals.

#### Scenario: Notebook environment includes reporting tools
- **WHEN** a user installs the documented notebook/reporting dependency environment
- **THEN** Jupytext notebook execution and Lets-Plot rendering dependencies are available

#### Scenario: Setup documentation distinguishes runtime and reporting environments
- **WHEN** a user reads the setup documentation
- **THEN** it identifies the core pipeline setup separately from the notebook/reporting setup

### Requirement: Notebook-only presentation helpers stay outside core package
Notebook-only plotting and display helper code SHALL live outside `src/payroll_anomaly_ranking` unless it provides reusable non-visual analytical outputs needed by downstream pipelines.

#### Scenario: Notebook helpers are isolated from runtime package
- **WHEN** shared notebook presentation code is needed
- **THEN** it is implemented in notebook-owned sources such as `notebooks/support/` rather than in the core runtime package

#### Scenario: Analytical data prep remains reusable when appropriate
- **WHEN** tabular diagnostics or queue summaries are useful to downstream pipelines independent of plotting
- **THEN** they remain available from core modules as Polars DataFrames without requiring notebook/reporting dependencies
