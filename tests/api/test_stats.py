"""Snapshot tests for ETable model statistics."""

import pytest
from helpers import OUTPUT_TYPES, render_table

import maketables as mt


class TestETableModelStats:
    """Snapshot tests for model_stats variations."""

    @pytest.mark.parametrize("output_type", OUTPUT_TYPES)
    @pytest.mark.parametrize(
        "model_stats, model_stats_labels",
        [
            pytest.param(["N", "r2", "adj_r2", "rmse"], None, id="extended"),
            pytest.param(["N"], None, id="minimal"),
            pytest.param(["N", "r2", "se_type"], None, id="with_se_type"),
            pytest.param(
                ["N", "r2"],
                {"N": "Sample Size", "r2": "R-squared"},
                id="custom_labels",
            ),
            pytest.param(["N", "aic", "bic"], None, id="aic_bic"),
        ],
    )
    def test_model_stats(
        self,
        fitted_model,
        snapshot,
        model_stats,
        model_stats_labels,
        output_type,
    ):
        """Model statistics variations."""
        table = mt.ETable(
            [fitted_model],
            model_stats=model_stats,
            model_stats_labels=model_stats_labels,
        )
        assert render_table(table, output_type) == snapshot
