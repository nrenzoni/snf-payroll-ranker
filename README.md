# SNF Payroll Ranker

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![uv](https://img.shields.io/badge/uv-managed-purple.svg)](https://docs.astral.sh/uv/)
[![Ruff](https://img.shields.io/badge/ruff-formatted-brightgreen.svg)](https://docs.astral.sh/ruff/)
[![Pyrefly](https://img.shields.io/badge/pyrefly-checked-blueviolet.svg)](https://pyrefly.org/)

A privacy-safe machine learning portfolio project for prioritizing risky SNF payroll records using synthetic data, leakage-safe temporal validation, and an employee-pay-cycle scoring pipeline.

---

<img width="688" height="384" alt="payroll system graphic" src="https://github.com/user-attachments/assets/5e003709-1684-4d39-94f6-135ef62e4bf4" />

---

```mermaid
flowchart LR
    classDef source fill:#F8FAFC,stroke:#64748B,color:#0F172A;
    classDef gate fill:#FEF2F2,stroke:#DC2626,color:#7F1D1D;
    classDef residual fill:#F0FDF4,stroke:#16A34A,color:#14532D;
    classDef model fill:#EFF6FF,stroke:#2563EB,color:#1E3A8A;
    classDef output fill:#FAF5FF,stroke:#9333EA,color:#581C87;

    synthetic[Synthetic payroll data]:::source
    rules[Hard-rule screening]:::gate
    excluded[Obvious violations removed]:::gate
    residual[Residual payroll records]:::residual
    features[Leakage-safe features]:::model
    ranking[ML ranking]:::model
    queue[Ranked review queue]:::output

    synthetic --> rules
    rules -->|rule hits| excluded
    rules -->|surviving records| residual
    residual --> features --> ranking --> queue
```

## Highlights

- Employee-pay-cycle payroll ranking pipeline built in Python with Polars, NumPy, and scikit-learn.
- Fully synthetic payroll data so the project is public, reproducible, and portfolio-safe.
- Temporal validation and historical-only feature engineering to avoid leakage.
- Jupytext notebook reporting with a single end-to-end public analysis notebook.

## Quick Start

```bash
uv sync
uv run python -m payroll_anomaly_ranking.pipeline
```

Optional notebook dependencies:

```bash
uv sync --extra notebooks
```

## What This Repo Contains

- `src/payroll_anomaly_ranking/`: runtime pipeline, feature engineering, scoring, and evaluation
- `notebooks/snf_payroll_ranker_report.py`: primary public analysis notebook
- `tests/`: smoke and integration coverage
- `openspec/`: versioned specs and design-change history

## Docs

- [Architecture](ARCHITECTURE.md)
- [Technical Decisions](DECISIONS.md)
- [Development Guide](docs/development.md)
- [Notebook Guide](notebooks/README.md)
- [Agent Workflow](AGENTS.md)

## Project Status

The project centers an employee-pay-cycle ranking library for production-oriented SNF payroll review research.

## Notebook Output

Rendered notebook outputs are published at:

**https://nrenzoni.github.io/snf-payroll-ranker/**
