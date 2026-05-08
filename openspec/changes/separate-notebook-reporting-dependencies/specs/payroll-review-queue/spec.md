## MODIFIED Requirements

### Requirement: Required business visuals
The notebooks SHALL include clean visuals or tables for payroll trend, gross pay distribution, overtime distribution, department payroll heatmap or table, score distribution, precision@K by review budget, dollars captured@K by review budget, model comparison, backtest metrics over time, and selected employee history for a flagged record. Notebook visual construction SHALL be notebook/reporting code rather than a required core runtime package dependency.

#### Scenario: Required visuals render from synthetic outputs
- **WHEN** the notebook sequence is run on a clean checkout with the documented notebook/reporting dependency environment
- **THEN** the required visuals or tables render using synthetic data and generated evaluation outputs
- **AND** notebooks that render LetsPlot visuals call `LetsPlot.setup_html()` before displaying those charts
- **AND** continuous distribution visuals use binned histograms or equivalent aggregation rather than one bar per raw numeric value
