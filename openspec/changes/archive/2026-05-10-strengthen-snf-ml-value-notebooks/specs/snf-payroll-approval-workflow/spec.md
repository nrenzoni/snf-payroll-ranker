## ADDED Requirements

### Requirement: Business-facing SNF ML value proof
The SNF case-study notebook SHALL demonstrate the operational value of automated hybrid approval ranking compared with administrator-style manual threshold review.

#### Scenario: Business proof compares same review capacity
- **WHEN** the SNF case-study notebook runs
- **THEN** it displays a business-facing comparison of manual thresholds and automated hybrid ranking at configured review budgets, including review volume, precision, recall, estimated exposure captured, false positives avoided, and missed high-risk exceptions where available

#### Scenario: Business narrative explains operational value
- **WHEN** a reviewer reads the SNF case-study notebook
- **THEN** narrative text explains how automated ranking changes the weekly approval process from broad single-field threshold chasing to context-rich exception prioritization

### Requirement: Case-study threshold miss evidence
The SNF case-study notebook SHALL show where manual thresholds miss or overflag records relative to automated hybrid ranking in the overtime and premium mismatch scenarios.

#### Scenario: Overtime threshold misses are shown
- **WHEN** overtime, double-shift, rest-gap, or staffing-pressure case-study outputs are displayed
- **THEN** the notebook identifies examples or summaries where manual overtime or total-hours thresholds miss review-worthy high-risk records captured by hybrid ranking

#### Scenario: Premium threshold misses are shown
- **WHEN** premium mismatch or shift differential case-study outputs are displayed
- **THEN** the notebook identifies examples or summaries where manual gross-pay or premium-dollar thresholds miss unsupported premium contexts captured by hybrid ranking
