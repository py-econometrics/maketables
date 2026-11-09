"""Snapshot tests for table statistics."""

import pandas as pd
import pytest
from helpers import OUTPUT_TYPES, render_table

import maketables as mt
from maketables.dtable import _is_dummy_series


class TestETableModelStats:
    """Snapshot tests for model_stats variations."""

    @pytest.mark.parametrize("output_type", OUTPUT_TYPES)
    @pytest.mark.parametrize(
        ("model_stats", "model_stats_labels"),
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

    @pytest.mark.parametrize(
        ("stats_order", "expected_rows"),
        [
            (None, ["Average", "Observations", "R²"]),
            ("cs", ["Average", "Observations", "R²"]),
            ("sc", ["Observations", "R²", "Average"]),
            ("c", ["Average"]),
            ("s", ["Observations", "R²"]),
            ("", []),
        ],
    )
    def test_stats_order(self, fitted_model, stats_order, expected_rows):
        """Order or hide built-in and custom model-statistic blocks."""
        table = mt.ETable(
            [fitted_model],
            model_stats=["N", "r2"],
            custom_model_stats={"Average": [1.23]},
            stats_order=stats_order,
        )

        if "stats" not in table.df.index.get_level_values(0):
            actual_rows = []
        else:
            actual_rows = table.df.xs("stats").index.tolist()
        assert actual_rows == expected_rows

    def test_stats_order_rejects_invalid_value(self, fitted_model):
        """Reject unsupported model-statistic block orders."""
        with pytest.raises(ValueError, match="stats_order"):
            mt.ETable([fitted_model], stats_order="invalid")


class TestBTableStats:
    """Snapshot tests for BTable statistics."""

    def test_accepts_list_group_for_column_combinations(
        self,
        btable_factorial_df,
        snapshot,
    ):
        """Accept list-valued groups for column combinations."""
        pytest.importorskip("pyfixest")
        table = mt.BTable(
            btable_factorial_df,
            vars=["x", "z"],
            group=["treatment", "period"],
            stats=["mean"],
        )

        assert table.df.to_csv().strip() == snapshot

    def test_byrow_splits_table_into_row_groups_with_independent_pvalues(
        self,
        btable_factorial_df,
        snapshot,
    ):
        """Byrow row-groups the table and tests balance separately within each group."""
        pytest.importorskip("pyfixest")
        df = btable_factorial_df.copy()
        # Alternate role within each treatment block (not aligned with it),
        # so both roles see both treatment levels and the p-value regression
        # has variation to estimate within every row-group.
        df["role"] = ["A", "B"] * 8
        table = mt.BTable(
            df,
            vars=["x", "z"],
            group="treatment",
            byrow="role",
            stats=["mean"],
        )

        assert table.df.to_csv().strip() == snapshot


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


def test_is_dummy_series_detects_two_unique_nonmissing_values(
    binary_type_df,
    snapshot,
):
    results = {
        col: _is_dummy_series(binary_type_df[col]) for col in binary_type_df.columns
    }

    assert results == snapshot


class _StatsResult:
    """Minimal plug-in result object with fixed statistics."""

    def __init__(self, stats):
        self._stats = stats

    @property
    def __maketables_coef_table__(self):
        return pd.DataFrame({"b": [0.5], "se": [0.1], "p": [0.01]}, index=["x"])

    def __maketables_stat__(self, key):
        return self._stats.get(key)


def test_model_stat_rows_use_one_format_per_row():
    models = [
        _StatsResult({"N": 100.0, "r2": 0.5, "rmse": 1.5, "aic": 1234.5, "n_folds": 5}),
        _StatsResult(
            {"N": 2500, "r2": 0.512, "rmse": 0.85, "aic": 12.0, "n_folds": 10}
        ),
    ]
    stats = mt.ETable(models, model_stats=["N", "r2", "rmse", "aic", "n_folds"]).df.loc[
        "stats"
    ]

    assert stats.to_numpy().tolist() == [
        ["100", "2,500"],
        ["0.500", "0.512"],
        ["1.500", "0.850"],
        ["1,234.500", "12.000"],
        ["5", "10"],
    ]
