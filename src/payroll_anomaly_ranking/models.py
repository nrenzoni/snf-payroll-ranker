from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.ensemble import IsolationForest

from payroll_anomaly_ranking.columns import (
    MODEL_FEATURE_COLUMNS,
    FeatureCol,
    PayrollCol,
    ReviewCol,
    RuleCol,
    ScoreCol,
)
from payroll_anomaly_ranking.config import PayrollConfig

FEATURE_COLUMNS = MODEL_FEATURE_COLUMNS


def temporal_split(
    payroll: pl.DataFrame,
    validation_periods: int = 4,
    test_periods: int = 4,
) -> dict[str, pl.DataFrame]:
    periods = sorted(payroll.get_column(PayrollCol.PAY_PERIOD_INDEX).unique().to_list())
    test_start = periods[-test_periods]
    validation_start = periods[-(test_periods + validation_periods)]
    return {
        "train": payroll.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) < validation_start),
        "validation": payroll.filter(
            (pl.col(PayrollCol.PAY_PERIOD_INDEX) >= validation_start)
            & (pl.col(PayrollCol.PAY_PERIOD_INDEX) < test_start),
        ),
        "test": payroll.filter(pl.col(PayrollCol.PAY_PERIOD_INDEX) >= test_start),
    }


def add_statistical_scores(payroll: pl.DataFrame) -> pl.DataFrame:
    return payroll.with_columns(
        pl.max_horizontal(
            pl.col(FeatureCol.GROSS_PAY_ROBUST_Z).fill_null(0) / 8,
            pl.col(FeatureCol.GROSS_PAY_MAD_SCORE).fill_null(0) / 10,
            pl.col(FeatureCol.PEER_GROSS_DEVIATION_RATIO).abs().fill_null(0) / 2,
            pl.col(FeatureCol.PEER_OVERTIME_DEVIATION_RATIO).abs().fill_null(0) / 6,
        )
        .clip(0, 1)
        .alias(ScoreCol.STATISTICAL_SCORE),
        pl.max_horizontal(
            pl.col(FeatureCol.GROSS_PAY_ROBUST_Z).fill_null(0) / 8,
            pl.col(FeatureCol.GROSS_PAY_PCT_CHANGE).abs().fill_null(0) / 2,
        )
        .clip(0, 1)
        .alias(ScoreCol.HISTORY_SCORE),
        pl.max_horizontal(
            pl.col(FeatureCol.PEER_GROSS_DEVIATION_RATIO).abs().fill_null(0) / 2,
            pl.col(FeatureCol.PEER_OVERTIME_DEVIATION_RATIO).abs().fill_null(0) / 6,
        )
        .clip(0, 1)
        .alias(ScoreCol.PEER_SCORE),
    )


def add_isolation_forest_scores(
    payroll: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> pl.DataFrame:
    splits = temporal_split(payroll)
    train = _feature_matrix(splits["train"])
    all_features = _feature_matrix(payroll)
    model = IsolationForest(
        n_estimators=100,
        contamination=0.03,
        random_state=config.seed,
    )
    model.fit(train)
    raw = -model.decision_function(all_features)
    return payroll.with_columns(pl.Series(ScoreCol.ML_SCORE, _minmax(raw)))


def add_hybrid_scores(
    payroll: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> pl.DataFrame:
    expected_gross = pl.coalesce(
        pl.col(FeatureCol.GROSS_PAY_ROLLING_MEDIAN),
        pl.col(FeatureCol.PEER_GROSS_MEDIAN),
        pl.col(PayrollCol.GROSS_PAY),
    )
    expected_deductions = pl.col(PayrollCol.GROSS_PAY) * pl.coalesce(
        pl.col(FeatureCol.DEDUCTION_RATIO_ROLLING_MEDIAN),
        pl.lit(0.22),
    )
    exposure = pl.max_horizontal(
        (pl.col(PayrollCol.GROSS_PAY) - expected_gross).clip(0, None),
        (
            pl.col(PayrollCol.GROSS_PAY)
            - pl.col(FeatureCol.PEER_GROSS_MEDIAN).fill_null(expected_gross)
        ).clip(0, None),
        (
            (
                pl.col(PayrollCol.OVERTIME_HOURS)
                - pl.col(FeatureCol.OVERTIME_ROLLING_MEDIAN).fill_null(0)
            ).clip(0, None)
            * pl.col(PayrollCol.PAY_RATE)
            * 1.5
        ),
        pl.col(PayrollCol.MANUAL_ADJUSTMENT).abs().fill_null(0),
        (expected_deductions - pl.col(PayrollCol.DEDUCTIONS).fill_null(0)).clip(
            0,
            None,
        ),
        pl.col(PayrollCol.GROSS_PAY).abs().fill_null(0)
        * (pl.col(RuleCol.SEVERITY_SCORE).fill_null(0) / 100),
    )
    scored = payroll.with_columns(
        (pl.col(RuleCol.SEVERITY_SCORE) / 100).clip(0, 1).alias(ScoreCol.RULE_SCORE),
        exposure.alias(ScoreCol.ESTIMATED_EXPOSURE),
        (exposure / pl.col(PayrollCol.GROSS_PAY).abs().clip(1, None))
        .clip(0, 1)
        .alias(ScoreCol.EXPOSURE_SCORE),
    )
    scored = scored.with_columns(
        pl.col(ScoreCol.EXPOSURE_SCORE).alias(ScoreCol.DOLLAR_SCORE),
    )
    weights = config.hybrid_weights
    return scored.with_columns(
        sum(
            pl.col(name).fill_null(0) * weight for name, weight in weights.items()
        ).alias(ScoreCol.FINAL_ANOMALY_SCORE),
    ).with_columns(
        pl.col(ScoreCol.FINAL_ANOMALY_SCORE)
        .rank("ordinal", descending=True)
        .over(PayrollCol.PAY_PERIOD_INDEX)
        .alias(ScoreCol.PAY_PERIOD_RANK),
    )


def score_payroll(
    payroll: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> pl.DataFrame:
    scored = add_hybrid_scores(
        add_isolation_forest_scores(add_statistical_scores(payroll), config),
        config,
    )
    return add_uncertainty_scores(scored, config)


def add_uncertainty_scores(
    scored: pl.DataFrame,
    config: PayrollConfig = PayrollConfig(),
) -> pl.DataFrame:
    base = scored.sort([PayrollCol.PAY_PERIOD_INDEX, PayrollCol.RECORD_ID])
    rows = base.to_dicts()
    feature_matrix = _feature_matrix(base)
    by_period = _rows_by_period(rows)
    feature_index_by_record = {
        row[PayrollCol.RECORD_ID]: index for index, row in enumerate(rows)
    }
    uncertainty_rows: list[dict[str, object]] = []
    for period in sorted(by_period):
        target_rows = by_period[period]
        references = _prior_reference_rows(
            rows,
            period,
            config.reference_window_periods,
        )
        reference_scores = [
            float(row[ScoreCol.FINAL_ANOMALY_SCORE] or 0.0) for row in references
        ]
        reference_features = np.array(
            [
                feature_matrix[feature_index_by_record[row[PayrollCol.RECORD_ID]]]
                for row in references
            ],
        )
        target_features = np.array(
            [
                feature_matrix[feature_index_by_record[row[PayrollCol.RECORD_ID]]]
                for row in target_rows
            ],
        )
        bootstrap = _bootstrap_intervals(reference_features, target_features, config)
        ood_distance_scores = _nearest_neighbor_uncertainty(
            reference_features,
            target_features,
        )
        for index, row in enumerate(target_rows):
            gross_interval = _expected_gross_pay_interval(row, references)
            conformal = _conformal_context(
                float(row[ScoreCol.FINAL_ANOMALY_SCORE] or 0.0),
                reference_scores,
            )
            peer_uncertainty = _sample_size_uncertainty(
                int(row.get(FeatureCol.EFFECTIVE_PEER_REFERENCE_SIZE) or 0),
                target=25,
            )
            history_uncertainty = _sample_size_uncertainty(
                int(row.get(FeatureCol.PRIOR_EMPLOYEE_PAY_PERIOD_COUNT) or 0),
                target=config.reference_window_periods,
            )
            data_quality, data_quality_drivers = _data_quality_uncertainty(row)
            ood, ood_drivers = _ood_uncertainty(
                row,
                references,
                ood_distance_scores[index],
                config,
            )
            ensemble = _ensemble_disagreement(row, config)
            interval_uncertainty = _interval_uncertainty(gross_interval)
            components = {
                ScoreCol.ENSEMBLE_DISAGREEMENT_UNCERTAINTY: ensemble,
                ScoreCol.BOOTSTRAP_INTERVAL_UNCERTAINTY: bootstrap[index]["width"],
                ScoreCol.EXPECTED_GROSS_PAY_INTERVAL_WIDTH: interval_uncertainty,
                ScoreCol.PEER_GROUP_UNCERTAINTY: peer_uncertainty,
                ScoreCol.EMPLOYEE_HISTORY_UNCERTAINTY: history_uncertainty,
                ScoreCol.DATA_QUALITY_UNCERTAINTY: data_quality,
                ScoreCol.OOD_UNCERTAINTY: ood,
            }
            composite = _weighted_composite(
                components,
                config.uncertainty_component_weights,
            )
            drivers = _uncertainty_drivers(
                components,
                data_quality_drivers + ood_drivers,
            )
            uncertainty_rows.append(
                {
                    PayrollCol.RECORD_ID: row[PayrollCol.RECORD_ID],
                    ScoreCol.ENSEMBLE_DISAGREEMENT_UNCERTAINTY: ensemble,
                    ScoreCol.BOOTSTRAP_SCORE_P10: bootstrap[index]["p10"],
                    ScoreCol.BOOTSTRAP_SCORE_P90: bootstrap[index]["p90"],
                    ScoreCol.BOOTSTRAP_SCORE_STD: bootstrap[index]["std"],
                    ScoreCol.BOOTSTRAP_INTERVAL_UNCERTAINTY: bootstrap[index]["width"],
                    ScoreCol.CONFORMAL_P_VALUE: conformal["p_value"],
                    ScoreCol.CONFORMAL_PERCENTILE: conformal["percentile"],
                    ScoreCol.EXPECTED_GROSS_PAY_P10: gross_interval["p10"],
                    ScoreCol.EXPECTED_GROSS_PAY_P50: gross_interval["p50"],
                    ScoreCol.EXPECTED_GROSS_PAY_P90: gross_interval["p90"],
                    ScoreCol.EXPECTED_GROSS_PAY_INTERVAL_WIDTH: gross_interval["width"],
                    ScoreCol.GROSS_PAY_EXCESS_VS_P90: gross_interval["excess"],
                    ScoreCol.PEER_GROUP_UNCERTAINTY: peer_uncertainty,
                    ScoreCol.EMPLOYEE_HISTORY_UNCERTAINTY: history_uncertainty,
                    ScoreCol.DATA_QUALITY_UNCERTAINTY: data_quality,
                    ScoreCol.OOD_UNCERTAINTY: ood,
                    ScoreCol.COMPOSITE_UNCERTAINTY_SCORE: composite,
                    ReviewCol.UNCERTAINTY_BUCKET: _uncertainty_bucket(
                        composite,
                        config,
                    ),
                    ReviewCol.PRIMARY_UNCERTAINTY_REASON: drivers[0]
                    if drivers
                    else "Stable recent comparison context",
                    ReviewCol.UNCERTAINTY_DRIVERS: "; ".join(drivers)
                    if drivers
                    else "none",
                },
            )
    uncertainty = pl.DataFrame(uncertainty_rows, infer_schema_length=None)
    return base.join(uncertainty, on=PayrollCol.RECORD_ID, how="left")


def _feature_matrix(frame: pl.DataFrame) -> np.ndarray:
    return frame.select(
        [pl.col(column).cast(pl.Float64).fill_null(0) for column in FEATURE_COLUMNS],
    ).to_numpy()


def _minmax(values: np.ndarray) -> np.ndarray:
    minimum = values.min()
    maximum = values.max()
    if maximum == minimum:
        return np.zeros_like(values)
    return (values - minimum) / (maximum - minimum)


def _rows_by_period(
    rows: list[dict[str, object]],
) -> dict[int, list[dict[str, object]]]:
    by_period: dict[int, list[dict[str, object]]] = {}
    for row in rows:
        by_period.setdefault(int(row[PayrollCol.PAY_PERIOD_INDEX]), []).append(row)
    return by_period


def _prior_reference_rows(
    rows: list[dict[str, object]],
    period: int,
    window: int,
) -> list[dict[str, object]]:
    return [
        row
        for row in rows
        if period - window <= int(row[PayrollCol.PAY_PERIOD_INDEX]) < period
    ]


def _ensemble_disagreement(row: dict[str, object], config: PayrollConfig) -> float:
    values = []
    weights = []
    for score_name, weight in config.hybrid_weights.items():
        if score_name in row and row[score_name] is not None:
            values.append(float(row[score_name]))
            weights.append(float(weight))
    if len(values) < 2:
        return 0.0
    value_array = np.array(values)
    weight_array = np.array(weights) / max(sum(weights), 1e-9)
    average = float(np.average(value_array, weights=weight_array))
    variance = float(np.average((value_array - average) ** 2, weights=weight_array))
    return float(np.clip(np.sqrt(variance) * 2.0, 0.0, 1.0))


def _bootstrap_intervals(
    reference_features: np.ndarray,
    target_features: np.ndarray,
    config: PayrollConfig,
) -> list[dict[str, float | None]]:
    empty = [
        {"p10": None, "p90": None, "std": None, "width": 0.0}
        for _ in range(len(target_features))
    ]
    if (
        len(reference_features) < config.bootstrap_min_reference_rows
        or len(target_features) == 0
        or config.bootstrap_samples <= 0
    ):
        return empty
    rng = np.random.default_rng(config.seed + len(reference_features))
    sample_scores = []
    for sample_index in range(config.bootstrap_samples):
        indices = rng.integers(0, len(reference_features), len(reference_features))
        model = IsolationForest(
            n_estimators=40,
            contamination=0.03,
            random_state=config.seed + sample_index,
        )
        model.fit(reference_features[indices])
        sample_scores.append(-model.decision_function(target_features))
    scores = np.vstack(sample_scores)
    lower, upper = np.percentile(scores, config.bootstrap_percentiles, axis=0)
    width = _minmax(upper - lower)
    std = np.std(scores, axis=0)
    return [
        {
            "p10": float(lower[index]),
            "p90": float(upper[index]),
            "std": float(std[index]),
            "width": float(width[index]),
        }
        for index in range(len(target_features))
    ]


def _conformal_context(
    score: float,
    reference_scores: list[float],
) -> dict[str, float | None]:
    if not reference_scores:
        return {"p_value": None, "percentile": None}
    more_extreme = sum(1 for reference in reference_scores if reference >= score)
    less_equal = sum(1 for reference in reference_scores if reference <= score)
    denominator = len(reference_scores) + 1
    return {
        "p_value": (more_extreme + 1) / denominator,
        "percentile": less_equal / len(reference_scores),
    }


def _expected_gross_pay_interval(
    row: dict[str, object],
    references: list[dict[str, object]],
) -> dict[str, float | None]:
    peer_values = [
        float(reference[PayrollCol.GROSS_PAY])
        for reference in references
        if _peer_key(reference) == _peer_key(row)
    ]
    values = (
        peer_values
        if len(peer_values) >= 5
        else [float(reference[PayrollCol.GROSS_PAY]) for reference in references]
    )
    if len(values) < 3:
        return {"p10": None, "p50": None, "p90": None, "width": None, "excess": None}
    p10, p50, p90 = np.percentile(np.array(values), [10, 50, 90])
    width = float(p90 - p10)
    excess = max(float(row[PayrollCol.GROSS_PAY]) - float(p90), 0.0)
    return {
        "p10": float(p10),
        "p50": float(p50),
        "p90": float(p90),
        "width": width,
        "excess": excess,
    }


def _sample_size_uncertainty(count: int, target: int) -> float:
    return float(np.clip(1 - (count / max(target, 1)), 0.0, 1.0))


def _data_quality_uncertainty(row: dict[str, object]) -> tuple[float, list[str]]:
    drivers = []
    if row.get(PayrollCol.DEDUCTIONS) is None:
        drivers.append("missing deductions")
    if float(row.get(PayrollCol.NET_PAY) or 0.0) < 0:
        drivers.append("negative net pay")
    if (
        float(row.get(PayrollCol.NET_PAY) or 0.0)
        > float(row.get(PayrollCol.GROSS_PAY) or 0.0) * 1.05
    ):
        drivers.append("net pay exceeds gross pay")
    if (
        float(row.get(PayrollCol.REGULAR_HOURS) or 0.0) <= 0
        and row.get(PayrollCol.EMPLOYMENT_STATUS) == "active"
    ):
        drivers.append("nonpositive active regular hours")
    if (
        float(row.get(PayrollCol.MANUAL_ADJUSTMENT) or 0.0)
        > float(row.get(PayrollCol.GROSS_PAY) or 0.0) * 0.25
    ):
        drivers.append("large manual adjustment")
    return float(min(len(drivers) * 0.25, 1.0)), drivers


def _nearest_neighbor_uncertainty(
    reference_features: np.ndarray,
    target_features: np.ndarray,
) -> list[float]:
    if len(reference_features) < 3 or len(target_features) == 0:
        return [0.0 for _ in range(len(target_features))]
    mean = reference_features.mean(axis=0)
    std = reference_features.std(axis=0)
    std[std == 0] = 1.0
    reference = (reference_features - mean) / std
    target = (target_features - mean) / std
    distances = []
    for target_row in target:
        nearest = np.sqrt(((reference - target_row) ** 2).mean(axis=1)).min()
        distances.append(float(nearest))
    if max(distances) == min(distances):
        return [0.0 for _ in distances]
    threshold = float(np.percentile(distances, 75)) or 1.0
    return [
        float(np.clip(distance / (threshold * 2), 0.0, 1.0)) for distance in distances
    ]


def _ood_uncertainty(
    row: dict[str, object],
    references: list[dict[str, object]],
    distance_score: float,
    config: PayrollConfig,
) -> tuple[float, list[str]]:
    drivers = []
    pay_code = row.get(PayrollCol.PAY_CODE)
    reference_pay_codes = [
        reference.get(PayrollCol.PAY_CODE) for reference in references
    ]
    pay_code_count = reference_pay_codes.count(pay_code)
    combo_count = sum(
        1
        for reference in references
        if reference.get(PayrollCol.PAY_CODE) == pay_code
        and reference.get(PayrollCol.PAY_TYPE) == row.get(PayrollCol.PAY_TYPE)
        and reference.get(PayrollCol.DEPARTMENT) == row.get(PayrollCol.DEPARTMENT)
    )
    if references and pay_code_count == 0:
        drivers.append("unseen pay code")
    elif references and pay_code_count <= config.ood_rare_pay_code_threshold:
        drivers.append("rare pay code")
    if references and combo_count <= config.ood_rare_pay_code_threshold:
        drivers.append("rare pay-code peer combination")
    if float(row.get(PayrollCol.OVERTIME_HOURS) or 0.0) > 60:
        drivers.append("out-of-range overtime")
    if float(row.get(PayrollCol.GROSS_PAY) or 0.0) <= 0:
        drivers.append("out-of-range gross pay")
    if distance_score >= config.ood_nearest_neighbor_percentile:
        drivers.append("distant from recent feature neighbors")
    categorical_score = min(len(drivers) * 0.22, 0.75)
    return float(np.clip(max(categorical_score, distance_score), 0.0, 1.0)), drivers


def _interval_uncertainty(interval: dict[str, float | None]) -> float:
    width = interval.get("width")
    p50 = interval.get("p50")
    if width is None or p50 is None:
        return 0.75
    return float(np.clip(float(width) / max(abs(float(p50)), 1.0), 0.0, 1.0))


def _weighted_composite(
    components: dict[ScoreCol, float],
    weights: dict[str, float],
) -> float:
    weighted = 0.0
    total = 0.0
    for name, value in components.items():
        weight = float(weights.get(name, 0.0))
        weighted += value * weight
        total += weight
    return float(np.clip(weighted / max(total, 1e-9), 0.0, 1.0))


def _uncertainty_bucket(score: float, config: PayrollConfig) -> str:
    medium, high = config.uncertainty_bucket_thresholds
    if score >= high:
        return "High"
    if score >= medium:
        return "Medium"
    return "Low"


def _uncertainty_drivers(
    components: dict[ScoreCol, float],
    issue_drivers: list[str],
) -> list[str]:
    labels = {
        ScoreCol.ENSEMBLE_DISAGREEMENT_UNCERTAINTY: "model signals disagree",
        ScoreCol.BOOTSTRAP_INTERVAL_UNCERTAINTY: "wide bootstrap score interval",
        ScoreCol.EXPECTED_GROSS_PAY_INTERVAL_WIDTH: "wide expected gross-pay interval",
        ScoreCol.PEER_GROUP_UNCERTAINTY: "small peer reference group",
        ScoreCol.EMPLOYEE_HISTORY_UNCERTAINTY: "limited employee history",
        ScoreCol.DATA_QUALITY_UNCERTAINTY: "data quality issue",
        ScoreCol.OOD_UNCERTAINTY: "out-of-distribution context",
    }
    strongest = sorted(components.items(), key=lambda item: item[1], reverse=True)[:3]
    component_drivers = [labels[name] for name, value in strongest if value >= 0.30]
    return [*component_drivers, *issue_drivers[:3]]


def _peer_key(row: dict[str, object]) -> tuple[object, ...]:
    return (
        row.get(PayrollCol.DEPARTMENT),
        row.get(PayrollCol.JOB_FAMILY),
        row.get(PayrollCol.PAY_TYPE),
        row.get(PayrollCol.LOCATION),
        row.get(FeatureCol.TENURE_BUCKET),
    )
