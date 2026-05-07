from __future__ import annotations

from collections.abc import Callable

import numpy as np
import polars as pl

from payroll_anomaly_ranking.columns import PayrollCol, ScoreCol
from payroll_anomaly_ranking.evaluation import (
    dollars_captured_at_k,
    precision_recall_at_k,
)

SCORE_SIGNALS = {
    "hybrid": ScoreCol.FINAL_ANOMALY_SCORE,
    "rule": ScoreCol.RULE_SCORE,
    "statistical": ScoreCol.STATISTICAL_SCORE,
    "ml": ScoreCol.ML_SCORE,
    "exposure": ScoreCol.EXPOSURE_SCORE,
}


def review_budget_interval_summary(
    scored: pl.DataFrame,
    k: int = 25,
    samples: int = 250,
    seed: int = 42,
) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(samples):
        sample = scored.sample(
            fraction=1.0,
            with_replacement=True,
            seed=int(rng.integers(1_000_000_000)),
        )
        metrics = {
            **precision_recall_at_k(sample, k),
            **dollars_captured_at_k(sample, k),
        }
        estimates.append(metrics)
    rows = []
    for metric in [
        "precision_at_k",
        "recall_at_k",
        "dollars_captured_at_k",
        "dollar_capture_rate",
    ]:
        values = np.array([row[metric] for row in estimates], dtype=float)
        rows.append(
            {
                "metric": metric,
                "k": k,
                "mean": float(values.mean()),
                "lower_95": float(np.quantile(values, 0.025)),
                "upper_95": float(np.quantile(values, 0.975)),
                "method": "bootstrap_posterior_simulation",
                "scope": "internal_evaluation_only",
            },
        )
    return pl.DataFrame(rows)


def component_superiority_summary(
    scored: pl.DataFrame,
    k: int = 25,
    samples: int = 100,
    seed: int = 42,
) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    wins: dict[tuple[str, str], int] = {}
    totals: dict[tuple[str, str], int] = {}
    names = list(SCORE_SIGNALS)
    for _ in range(samples):
        sample = scored.sample(
            fraction=1.0,
            with_replacement=True,
            seed=int(rng.integers(1_000_000_000)),
        )
        performance = {
            name: _precision_for_signal(sample, signal, k)
            for name, signal in SCORE_SIGNALS.items()
            if signal in sample.columns
        }
        for left in names:
            for right in names:
                if left == right or left not in performance or right not in performance:
                    continue
                key = (left, right)
                wins[key] = wins.get(key, 0) + int(
                    performance[left] > performance[right],
                )
                totals[key] = totals.get(key, 0) + 1
    return pl.DataFrame(
        [
            {
                "left_signal": left,
                "right_signal": right,
                "metric": f"precision_at_{k}",
                "superiority_probability": wins[(left, right)] / totals[(left, right)],
                "samples": totals[(left, right)],
            }
            for left, right in sorted(totals)
        ],
    )


def subgroup_diagnostics(
    scored: pl.DataFrame,
    dimensions: tuple[str, ...] = (
        PayrollCol.DEPARTMENT,
        PayrollCol.JOB_FAMILY,
        PayrollCol.LOCATION,
        PayrollCol.PAY_TYPE,
        PayrollCol.PAY_CODE,
        PayrollCol.JOB_LEVEL,
    ),
    k: int = 25,
) -> pl.DataFrame:
    rows = []
    global_rate = scored.select(pl.mean(PayrollCol.IS_ANOMALY)).item() or 0.0
    prior_strength = 25.0
    reviewed = scored.with_columns(
        (pl.col(ScoreCol.PAY_PERIOD_RANK) <= k).alias("reviewed"),
    )
    for dimension in dimensions:
        if dimension not in reviewed.columns:
            continue
        grouped = reviewed.group_by(dimension).agg(
            pl.len().alias("records"),
            pl.sum(PayrollCol.IS_ANOMALY).alias("true_anomalies"),
            pl.sum("reviewed").alias("reviewed_records"),
            ((pl.col("reviewed")) & (pl.col(PayrollCol.IS_ANOMALY) == 1))
            .sum()
            .alias("true_positive_reviews"),
            ((~pl.col("reviewed")) & (pl.col(PayrollCol.IS_ANOMALY) == 1))
            .sum()
            .alias("false_negatives"),
            ((pl.col("reviewed")) & (pl.col(PayrollCol.IS_ANOMALY) == 0))
            .sum()
            .alias("false_positives"),
        )
        for row in grouped.to_dicts():
            records = max(float(row["records"]), 1.0)
            raw_rate = float(row["true_anomalies"]) / records
            pooled = (float(row["true_anomalies"]) + global_rate * prior_strength) / (
                records + prior_strength
            )
            rows.append(
                {
                    "dimension": str(dimension),
                    "subgroup": str(row[dimension]),
                    **{key: row[key] for key in row if key != dimension},
                    "raw_anomaly_rate": raw_rate,
                    "pooled_anomaly_rate": pooled,
                    "shrinkage": pooled - raw_rate,
                    "lower_95": max(
                        0.0,
                        pooled
                        - 1.96 * np.sqrt(max(pooled * (1 - pooled), 0.0) / records),
                    ),
                    "upper_95": min(
                        1.0,
                        pooled
                        + 1.96 * np.sqrt(max(pooled * (1 - pooled), 0.0) / records),
                    ),
                },
            )
    return pl.DataFrame(rows, infer_schema_length=None)


def expected_pay_calibration(
    scored: pl.DataFrame,
    by: str | None = None,
) -> pl.DataFrame:
    required = {
        ScoreCol.EXPECTED_GROSS_PAY_P10,
        ScoreCol.EXPECTED_GROSS_PAY_P50,
        ScoreCol.EXPECTED_GROSS_PAY_P90,
    }
    if not required <= set(scored.columns):
        return pl.DataFrame()
    frame = scored.with_columns(
        (
            (pl.col(PayrollCol.GROSS_PAY) >= pl.col(ScoreCol.EXPECTED_GROSS_PAY_P10))
            & (pl.col(PayrollCol.GROSS_PAY) <= pl.col(ScoreCol.EXPECTED_GROSS_PAY_P90))
        ).alias("covered"),
        (
            pl.col(ScoreCol.EXPECTED_GROSS_PAY_P90)
            - pl.col(ScoreCol.EXPECTED_GROSS_PAY_P10)
        ).alias("interval_width"),
        (pl.col(PayrollCol.GROSS_PAY) - pl.col(ScoreCol.EXPECTED_GROSS_PAY_P90))
        .clip(0, None)
        .alias("excess_over_p90"),
        (pl.col(PayrollCol.GROSS_PAY) - pl.col(ScoreCol.EXPECTED_GROSS_PAY_P50)).alias(
            "residual",
        ),
    )
    group_cols = [by] if by and by in frame.columns else []
    return frame.group_by(group_cols).agg(
        pl.len().alias("records"),
        pl.mean("covered").alias("coverage"),
        pl.mean("interval_width").alias("avg_interval_width"),
        pl.mean("excess_over_p90").alias("avg_excess_over_p90"),
        pl.mean("residual").alias("avg_residual"),
    )


def robustness_summary(frames: dict[str, pl.DataFrame], k: int = 25) -> pl.DataFrame:
    rows = []
    queues: dict[str, set[int]] = {}
    for name, scored in frames.items():
        metrics = precision_recall_at_k(scored, k)
        queue = set(
            scored.sort(ScoreCol.FINAL_ANOMALY_SCORE, descending=True)
            .head(k)
            .get_column(PayrollCol.RECORD_ID)
            .to_list(),
        )
        queues[name] = queue
        rows.append({"setting": name, **metrics, "queue_size": len(queue)})
    for row in rows:
        overlaps = [
            _jaccard(queues[row["setting"]], other)
            for name, other in queues.items()
            if name != row["setting"]
        ]
        row["mean_queue_overlap"] = sum(overlaps) / len(overlaps) if overlaps else 1.0
        row["performance_instability"] = 1.0 - row["mean_queue_overlap"]
    return pl.DataFrame(rows)


def perturbation_sensitivity(
    scored: pl.DataFrame,
    perturb: Callable[[pl.DataFrame], pl.DataFrame],
    scorer: Callable[[pl.DataFrame], pl.DataFrame],
    threshold: float = 0.65,
) -> pl.DataFrame:
    baseline = scored.select(
        PayrollCol.RECORD_ID,
        ScoreCol.FINAL_ANOMALY_SCORE,
        ScoreCol.PAY_PERIOD_RANK,
    )
    perturbed = scorer(perturb(scored)).select(
        PayrollCol.RECORD_ID,
        pl.col(ScoreCol.FINAL_ANOMALY_SCORE).alias("perturbed_score"),
        pl.col(ScoreCol.PAY_PERIOD_RANK).alias("perturbed_rank"),
    )
    return baseline.join(perturbed, on=PayrollCol.RECORD_ID).with_columns(
        (pl.col("perturbed_score") - pl.col(ScoreCol.FINAL_ANOMALY_SCORE)).alias(
            "score_movement",
        ),
        (pl.col("perturbed_rank") - pl.col(ScoreCol.PAY_PERIOD_RANK)).alias(
            "rank_movement",
        ),
        (
            (pl.col(ScoreCol.FINAL_ANOMALY_SCORE) < threshold)
            & (pl.col("perturbed_score") >= threshold)
        ).alias("crossed_threshold"),
    )


def exposure_calibration(scored: pl.DataFrame) -> pl.DataFrame:
    if ScoreCol.ESTIMATED_EXPOSURE not in scored.columns:
        return pl.DataFrame()
    return (
        scored.group_by(PayrollCol.ANOMALY_CATEGORY)
        .agg(
            pl.len().alias("records"),
            pl.mean(ScoreCol.ESTIMATED_EXPOSURE).alias("avg_estimated_exposure"),
            pl.mean(PayrollCol.ANOMALY_DOLLARS).alias("avg_synthetic_anomaly_dollars"),
            pl.sum(ScoreCol.ESTIMATED_EXPOSURE).alias("total_estimated_exposure"),
            pl.sum(PayrollCol.ANOMALY_DOLLARS).alias("total_synthetic_anomaly_dollars"),
        )
        .with_columns(
            (
                pl.col("total_estimated_exposure")
                / (pl.col("total_synthetic_anomaly_dollars") + 1e-9)
            ).alias("exposure_to_synthetic_ratio"),
        )
    )


def _precision_for_signal(scored: pl.DataFrame, signal: str, k: int) -> float:
    ranked = (
        scored.sort([PayrollCol.PAY_PERIOD_INDEX, signal], descending=[False, True])
        .group_by(PayrollCol.PAY_PERIOD_INDEX)
        .head(k)
    )
    return ranked.filter(pl.col(PayrollCol.IS_ANOMALY) == 1).height / max(
        ranked.height,
        1,
    )


def _jaccard(left: set[int], right: set[int]) -> float:
    return len(left & right) / max(len(left | right), 1)
