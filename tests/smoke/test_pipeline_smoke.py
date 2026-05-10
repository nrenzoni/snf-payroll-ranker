from pathlib import Path

import pytest

from payroll_anomaly_ranking.columns import OutputName, PayrollCol
from payroll_anomaly_ranking.config import PayrollConfig
from payroll_anomaly_ranking.pipeline import (
    PipelineArtifactNotGeneratedError,
    PipelineIncludeConfig,
    run_pipeline,
)

pytestmark = pytest.mark.smoke


def _smoke_config(tmp_path: Path | None = None) -> PayrollConfig:
    data_dir = tmp_path / "data" if tmp_path else PayrollConfig().data_dir
    output_dir = tmp_path / "outputs" if tmp_path else PayrollConfig().output_dir
    return PayrollConfig(
        employee_count=30,
        pay_periods=10,
        review_budgets=(5,),
        bootstrap_samples=0,
        data_dir=data_dir,
        output_dir=output_dir,
    )


def test_pipeline_runs_end_to_end_without_leaking_review_truth() -> None:
    results = run_pipeline(_smoke_config())

    assert results.payroll.height > 0
    assert results.scored.height == results.payroll.height
    assert results.validation_failures.height == 0
    assert results.metrics.height == 1
    assert results.analyst_review_queue.height > 0
    assert results.facility_approval_summary.height > 0
    assert PayrollCol.FACILITY_ID in results.payroll.columns
    assert PayrollCol.SHIFT_ID in results.payroll.columns
    assert PayrollCol.PREMIUM_PAY in results.payroll.columns
    assert not {
        PayrollCol.IS_ANOMALY,
        PayrollCol.ANOMALY_CATEGORY,
        PayrollCol.ANOMALY_DOLLARS,
        "name",
        "email",
        "bank_account",
        "ssn",
    } & set(results.analyst_review_queue.columns)


def test_pipeline_output_writes_are_explicit(tmp_path: Path) -> None:
    config = _smoke_config(tmp_path)

    run_pipeline(config)

    assert not config.data_dir.exists()
    assert not config.output_dir.exists()

    run_pipeline(config, write_outputs=True)

    assert (config.data_dir / "synthetic_payroll.csv").exists()
    assert (config.output_dir / "evaluation" / "review_budget_metrics.csv").exists()
    assert (config.output_dir / "evaluation" / OutputName.ANALYST_REVIEW_QUEUE).exists()
    assert (config.output_dir / "evaluation" / OutputName.ADMIN_APPROVAL_QUEUE).exists()
    assert (
        config.output_dir / "evaluation" / OutputName.FACILITY_APPROVAL_SUMMARY
    ).exists()


def test_scored_only_pipeline_exposes_only_core_artifacts() -> None:
    results = run_pipeline(
        _smoke_config(),
        include=PipelineIncludeConfig.scored_only(),
    )

    assert results.payroll.height > 0
    assert results.labels.height > 0
    assert results.scored.height == results.payroll.height
    assert results.scenario_metadata["name"] == "default"
    with pytest.raises(PipelineArtifactNotGeneratedError, match="metrics"):
        results.metrics


def test_scored_only_pipeline_cannot_write_full_outputs(tmp_path: Path) -> None:
    config = _smoke_config(tmp_path)

    with pytest.raises(PipelineArtifactNotGeneratedError, match="metrics"):
        run_pipeline(
            config,
            write_outputs=True,
            include=PipelineIncludeConfig.scored_only(),
        )
