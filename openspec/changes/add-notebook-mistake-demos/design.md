## Context

The existing modeling notebook already explains temporal validation, review-budget metrics, model comparison, backtesting, category-level error analysis, and cost-aware interpretation. The requested change adds explicit teaching demos for common mistakes so readers can see the failure mode, not just read the recommendation.

The project uses Jupytext `.py` notebooks, Lets-plot visualizations, Polars dataframes, and a notebook-library pattern for reusable or complex logic. Existing modules already provide temporal splitting, Isolation Forest scoring, review-budget metrics, dollar capture, model comparison, and category error analysis.

## Goals / Non-Goals

**Goals:**

- Add notebook sections that cover each requested mistake with an anti-pattern, a corrected method, and visual evidence where the mistake is empirical.
- Keep examples reproducible with the existing synthetic payroll pipeline.
- Make the business interpretation explicit: anomaly ranking supports triage and review, not definitive fraud detection.
- Prefer existing scoring, evaluation, and charting utilities; add only small notebook-local or sibling-library helpers when repeated logic would otherwise clutter the notebook.
- Preserve the existing temporal-validation position: random splits may be shown only as a labeled anti-pattern, not as an accepted evaluation method.

**Non-Goals:**

- Do not replace the existing payroll scoring approach or change production-facing APIs.
- Do not claim real fraud labels or regulated audit conclusions from synthetic anomaly labels.
- Do not introduce new plotting or machine-learning dependencies.

## Decisions

- Extend `notebooks/03_modeling_evaluation_and_error_analysis.py` rather than creating a separate notebook. This keeps the demos next to the current evaluation narrative and avoids fragmenting the modeling lesson. Alternative considered: a new dedicated mistakes notebook; rejected because the existing notebook is already the evaluation entry point.
- Use side-by-side demonstration tables and Lets-plot charts for empirical mistakes, and use labeled wording comparisons for the fraud-claim mistake. This makes the anti-pattern and corrected method directly comparable without forcing a low-value plot for a language-governance issue. Alternative considered: requiring a plot for every mistake; rejected because overclaiming fraud detection is better demonstrated through claim language and interpretation boundaries.
- Use synthetic labels only as demonstration ground truth. This preserves the current framing that labels validate synthetic injected exceptions, not real-world fraud. Alternative considered: naming the target fraud; rejected because it would reinforce the overclaiming mistake being taught.
- Compute metric comparisons on held-out or later-period records when the lesson concerns model evaluation. This keeps the demos aligned with temporal validation rather than accidentally summarizing train-era rows. Alternative considered: using all scored records for convenience; rejected because it can blur the distinction between fitting, scoring, and evaluation.
- Make the Isolation Forest comparison about explicit assumptions rather than generic tuning. The corrected example should expose choices such as temporal training data, contamination/review-capacity assumptions, random seed stability, and operational metrics. Alternative considered: comparing defaults to an arbitrary parameter search; rejected because it teaches parameter chasing instead of payroll-fit evaluation.
- Keep heavier demo calculations in a sibling helper only if the notebook becomes repetitive or hard to read. This follows the notebook-library pattern without adding unnecessary abstraction for simple one-off cells. Alternative considered: putting all demo helpers in `src/`; rejected unless the logic becomes broadly reusable beyond this notebook.

## Risks / Trade-offs

- Demos may lengthen the modeling notebook → keep each mistake section concise and focused on one visual comparison.
- Random split and default-model anti-patterns can appear better on a single synthetic seed → use stable seeded examples, evaluate on later periods where applicable, and explain the demonstrated risk rather than relying on one metric as proof.
- Random split demos can conflict with the existing instruction to avoid random split framing → label random splits as an anti-pattern and pair them immediately with the temporal-validation correction.
- Several leakage mechanisms can be confounded in one random-split demo → distinguish row-split leakage from global feature baselines and same-period peer context in the narrative.
- ROC-AUC examples can be misleading if class imbalance is not visible → pair ROC-AUC with PR-AUC, Precision@K, false positives, and review-budget charts.
- False-positive analysis can overemphasize operational cost without acknowledging missed anomalies → compare false positives with recall, dollar capture, and queue budget.
- Business language can drift into fraud claims → use explicit wording that the workflow ranks review candidates and flags synthetic anomalies for demonstration only.
