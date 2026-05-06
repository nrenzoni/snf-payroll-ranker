## MODIFIED Requirements

### Requirement: Temporal validation explanation
The notebooks SHALL explain temporal validation and SHALL avoid endorsing random split framing. A notebook MAY show random row splits only as an explicitly labeled anti-pattern when it is immediately compared against temporal validation.

#### Scenario: Temporal validation is documented
- **WHEN** a reviewer reads the modeling and evaluation notebook
- **THEN** the notebook explains that payroll scoring is evaluated over time using prior periods and later periods rather than random row splits

#### Scenario: Random split anti-pattern is demonstrated
- **WHEN** the modeling and evaluation notebook demonstrates random train/test splitting
- **THEN** the random split is labeled as an anti-pattern and compared against temporal validation rather than presented as an accepted evaluation method
