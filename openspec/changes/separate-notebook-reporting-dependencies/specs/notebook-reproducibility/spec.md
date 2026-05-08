## MODIFIED Requirements

### Requirement: Clean notebook execution
The notebook sequence SHALL execute from a clean checkout without errors using the documented notebook/reporting dependency environment.

#### Scenario: Notebook sequence executes successfully
- **WHEN** the documented notebook execution command is run for each business-facing notebook after installing notebook/reporting dependencies
- **THEN** each notebook completes without traceback outputs or failed cells

### Requirement: Paired notebook outputs are refreshable
The internal diagnostic notebooks SHALL produce paired outputs that can be regenerated reproducibly using the documented notebook/reporting dependency environment.

#### Scenario: Paired outputs refresh reproducibly
- **WHEN** paired internal diagnostic notebooks or notebook-output refresh commands are run with a fixed seed after installing notebook/reporting dependencies
- **THEN** paired tables, plot inputs, scenario summaries, and generated artifacts are refreshed consistently and documented as reproducible outputs
