"""Snapshot tests for table statistics."""

import pytest

import maketables as mt
from helpers import normalize_html
from maketables.dtable import _is_binary_series


class TestETableModelStats:
    """Snapshot tests for model_stats variations."""

    def test_model_stats_extended_html(self, fitted_model, snapshot):
        """Extended statistics including adj_r2 and rmse."""
        table = mt.ETable([fitted_model], model_stats=["N", "r2", "adj_r2", "rmse"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_model_stats_extended_latex(self, fitted_model, snapshot):
        """Extended statistics including adj_r2 and rmse."""
        table = mt.ETable([fitted_model], model_stats=["N", "r2", "adj_r2", "rmse"])
        assert table.make(type="tex") == snapshot

    def test_model_stats_minimal_html(self, fitted_model, snapshot):
        """Minimal statistics (only N)."""
        table = mt.ETable([fitted_model], model_stats=["N"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_model_stats_minimal_latex(self, fitted_model, snapshot):
        """Minimal statistics (only N)."""
        table = mt.ETable([fitted_model], model_stats=["N"])
        assert table.make(type="tex") == snapshot

    def test_model_stats_with_se_type_html(self, fitted_model, snapshot):
        """Include standard error type."""
        table = mt.ETable([fitted_model], model_stats=["N", "r2", "se_type"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_model_stats_with_se_type_latex(self, fitted_model, snapshot):
        """Include standard error type."""
        table = mt.ETable([fitted_model], model_stats=["N", "r2", "se_type"])
        assert table.make(type="tex") == snapshot

    def test_model_stats_custom_labels_html(self, fitted_model, snapshot):
        """Custom labels for model statistics."""
        table = mt.ETable(
            [fitted_model],
            model_stats=["N", "r2"],
            model_stats_labels={"N": "Sample Size", "r2": "R-squared"},
        )
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_model_stats_custom_labels_latex(self, fitted_model, snapshot):
        """Custom labels for model statistics."""
        table = mt.ETable(
            [fitted_model],
            model_stats=["N", "r2"],
            model_stats_labels={"N": "Sample Size", "r2": "R-squared"},
        )
        assert table.make(type="tex") == snapshot

    def test_model_stats_aic_bic_html(self, fitted_model, snapshot):
        """Information criteria (AIC, BIC)."""
        table = mt.ETable([fitted_model], model_stats=["N", "aic", "bic"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_model_stats_aic_bic_latex(self, fitted_model, snapshot):
        """Information criteria (AIC, BIC)."""
        table = mt.ETable([fitted_model], model_stats=["N", "aic", "bic"])
        assert table.make(type="tex") == snapshot


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


def test_is_binary_series_detects_two_unique_nonmissing_values(
    binary_type_df,
    snapshot,
):
    results = {
        col: _is_binary_series(binary_type_df[col]) for col in binary_type_df.columns
    }

    assert results == snapshot
