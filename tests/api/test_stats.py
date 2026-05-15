"""Snapshot tests for table statistics."""

import pytest
from helpers import OUTPUT_TYPES, render_table

import maketables as mt
from maketables.dtable import _is_binary_series


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


def test_dtable_mean_std_suppresses_std_for_binary_variables(
    dtable_binary_df,
    snapshot,
):
    table = mt.DTable(
        dtable_binary_df,
        vars=["binary", "continuous"],
        stats=["mean_std"],
    )

    assert table.df.to_csv().strip() == snapshot


def test_dtable_mean_newline_std_suppresses_std_for_grouped_binary_variables(
    dtable_binary_df,
    snapshot,
):
    table = mt.DTable(
        dtable_binary_df,
        vars=["binary", "continuous"],
        stats=["mean_newline_std"],
        bycol=["group"],
    )

    assert table.df.to_csv().strip() == snapshot


def test_btable_mean_std_suppresses_std_for_binary_variables(
    dtable_binary_df,
    snapshot,
):
    pytest.importorskip("pyfixest")
    table = mt.BTable(
        dtable_binary_df,
        vars=["binary", "continuous"],
        group="group",
        stats=["mean_std"],
    )

    assert table.df.to_csv().strip() == snapshot


def test_btable_accepts_list_group_for_column_combinations(
    btable_factorial_df,
    snapshot,
):
    pytest.importorskip("pyfixest")
    table = mt.BTable(
        btable_factorial_df,
        vars=["x", "z"],
        group=["treatment", "period"],
        stats=["mean"],
    )

    assert table.df.to_csv().strip() == snapshot


def test_is_binary_series_detects_two_unique_nonmissing_values(
    binary_type_df,
    snapshot,
):
    results = {
        col: _is_binary_series(binary_type_df[col]) for col in binary_type_df.columns
    }

    assert results == snapshot
