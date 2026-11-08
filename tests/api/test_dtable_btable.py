import numpy as np
import pandas as pd
import pytest

import maketables as mt
from maketables.dtable import _format_mean_std, _is_dummy_series, _relabel_index


@pytest.fixture
def df():
    rng = np.random.default_rng(0)
    n = 120
    g = np.repeat(["a", "b", "c"], n // 3)
    return pd.DataFrame(
        {
            "x": rng.normal(size=n) + (g == "b") * 2.0,
            "y": rng.normal(10, 2, size=n),
            "dummy": rng.integers(0, 2, size=n),
            "g": g,
            "h": np.tile(["u", "v"], n // 2),
            "txt": ["s"] * n,
        }
    )


class TestDTable:
    """DTable grouping, stats and formatting."""

    def test_default_stats(self, df):
        t = mt.DTable(df, vars=["x", "y"])
        assert list(t.df.index) == ["x", "y"]
        assert list(t.df.columns) == ["N", "Mean", "Std. Dev."]
        assert t.df.loc["y", "Mean"] == f"{df['y'].mean():.2f}"

    def test_custom_stats_and_labels(self, df):
        t = mt.DTable(
            df,
            vars=["x"],
            stats=["min", "max", "median", "var"],
            stats_labels={"min": "Minimum"},
            labels={"x": "Var X"},
        )
        assert list(t.df.columns) == ["Minimum", "Max", "Median", "Variance"]
        assert list(t.df.index) == ["Var X"]
        assert t.df.iloc[0, 0] == f"{df['x'].min():.2f}"

    def test_digits_and_format_spec(self, df):
        t = mt.DTable(
            df,
            vars=["x", "y"],
            stats=["count", "mean"],
            digits=4,
            format_spec={"count": "d", ("y", "mean"): ".1f", "x": ".3f"},
        )
        assert t.df.loc["y", "N"] == "120"
        assert t.df.loc["x", "N"] == "120.000"  # var spec beats stat spec
        assert t.df.loc["y", "Mean"] == f"{df['y'].mean():.1f}"
        assert t.df.loc["x", "Mean"] == f"{df['x'].mean():.3f}"

    def test_mean_std_combined(self, df):
        t = mt.DTable(df, vars=["x", "dummy"], stats=["mean_std"])
        x_cell = t.df.loc["x"].iloc[0]
        assert x_cell == f"{df['x'].mean():.2f} ({df['x'].std():.2f})"
        # std suppressed for dummies
        assert t.df.loc["dummy"].iloc[0] == f"{df['dummy'].mean():.2f}"
        t2 = mt.DTable(df, vars=["x"], stats=["mean_newline_std"])
        assert "\n(" in t2.df.iloc[0, 0]

    def test_byrow(self, df):
        t = mt.DTable(df, vars=["x", "y"], byrow="g")
        assert isinstance(t.df.index, pd.MultiIndex)
        assert set(t.df.index.get_level_values(0)) == {"a", "b", "c"}
        expected = f"{df.loc[df.g == 'b', 'x'].mean():.2f}"
        assert t.df.loc[("b", "x"), "Mean"] == expected

    def test_bycol(self, df):
        t = mt.DTable(df, vars=["x", "y"], bycol=["g"], stats=["mean", "std"])
        cols = t.df.columns
        assert isinstance(cols, pd.MultiIndex)
        assert cols.nlevels == 2
        assert set(cols.get_level_values(0)) == {"a", "b", "c"}
        assert list(t.df.index) == ["x", "y"]

    def test_bycol_hide_stats_notes(self, df):
        t = mt.DTable(df, vars=["x"], bycol=["g"], hide_stats=True)
        assert t.df.columns.nlevels == 1
        assert "Displayed statistics are N, Mean, Std. Dev." in t.notes
        t2 = mt.DTable(df, vars=["x"], bycol=["g"], hide_stats=True, notes="mine")
        assert t2.notes == "mine"

    def test_byrow_and_bycol(self, df):
        t = mt.DTable(df, vars=["x"], byrow="h", bycol=["g"], stats=["mean"])
        assert isinstance(t.df.index, pd.MultiIndex)
        assert t.df.columns.nlevels == 2

    def test_counts_row_below(self, df):
        t = mt.DTable(df, vars=["x", "y"], counts_row_below=True)
        assert list(t.df.columns) == ["Mean", "Std. Dev."]
        assert t.df.index[-1] == ("nobs", "N")
        assert float(t.df.loc[("nobs", "N")].iloc[0]) == 120

    def test_counts_row_below_added_and_grouped(self, df):
        t = mt.DTable(df, vars=["x"], stats=["mean"], counts_row_below=True)
        assert t.df.index[-1] == ("nobs", "N")
        tg = mt.DTable(df, vars=["x", "y"], bycol=["g"], counts_row_below=True)
        assert "N" in str(tg.df.index[-1]) or "N" in str(tg.df.columns[-1])

    def test_counts_row_below_unbalanced(self, df):
        df2 = df.copy()
        df2.loc[:5, "x"] = np.nan
        t = mt.DTable(df2, vars=["x", "y"], counts_row_below=True)
        assert "N" in t.df.columns
        assert not isinstance(t.df.index, pd.MultiIndex)

    def test_counts_row_below_ignored_with_byrow(self, df):
        t = mt.DTable(df, vars=["x"], byrow="g", counts_row_below=True)
        assert "N" in t.df.columns

    def test_missing_values_dash(self):
        data = pd.DataFrame({"x": [1.0, 2.0], "y": [np.nan, np.nan]})
        t = mt.DTable(data, vars=["x", "y"], stats=["mean", "std"])
        assert t.df.loc["y", "Mean"] == "-"

    def test_format_number(self, df):
        f = mt.DTable(df, vars=["x"])._format_number  # noqa: SLF001
        assert f(float("nan")) == "-"
        assert f(0.0000123) == "0.000012"
        assert f(5.0) == "5.00"
        assert f(12345.6) == "12,346"
        assert f(3.4, "d") == "3"
        assert f(2.5, ".1e") == "2.5e+00"
        # invalid spec falls back to default
        assert f(2.5, "zz") == "2.50"

    def test_type_df(self, df):
        assert isinstance(mt.DTable(df, vars=["x"], type="df").df, pd.DataFrame)

    @pytest.mark.parametrize(
        ("kwargs", "match"),
        [
            ({"vars": ["txt"]}, "numerical"),
            ({"vars": ["x"], "type": "foo"}, "type must"),
            ({"vars": ["x"], "byrow": "nope"}, "byrow"),
            ({"vars": ["x"], "bycol": ["nope"]}, "bycol"),
        ],
    )
    def test_errors(self, df, kwargs, match):
        with pytest.raises(ValueError, match=match):
            mt.DTable(df, **kwargs)

    def test_df_attrs_labels(self, df):
        df = df.copy()
        df.attrs["variable_labels"] = {"x": "Label from attrs"}
        t = mt.DTable(df, vars=["x"])
        assert list(t.df.index) == ["Label from attrs"]

    def test_make_outputs(self, df):
        t = mt.DTable(df, vars=["x", "y"], bycol=["g"])
        assert t.make(type="gt") is not None
        assert "tabular" in t.make(type="tex")


class TestHelpers:
    """Module-level helper functions."""

    def test_is_dummy(self):
        assert _is_dummy_series(pd.Series([0, 1, 1]))
        assert _is_dummy_series(pd.Series([True, False]))
        assert not _is_dummy_series(pd.Series([0, 1, 2]))
        assert not _is_dummy_series(pd.Series(["a", "b"]))

    def test_relabel_index(self):
        assert _relabel_index(["a", "b"], {"a": "A"}) == ["A", "b"]
        mi = pd.MultiIndex.from_tuples([("a", "mean")])
        assert list(_relabel_index(mi, {"a": "A"})) == [("A", "mean")]
        assert list(_relabel_index(mi, {"a": "A"}, {"mean": "Mean"})) == [("A", "Mean")]
        assert _relabel_index(["mean"], None, {"mean": "M"}) == ["M"]

    def test_format_mean_std_plain(self):
        s = pd.Series([1.0, 2.0, 3.0])
        assert _format_mean_std(s, newline=False) == "2.00 (1.00)"
        assert _format_mean_std(s, newline=True) == "2.00\n(1.00)"
        assert _format_mean_std(s, suppress_std=True) == "2.00"


class TestBTable:
    """BTable group-difference p-values and notes."""

    @pytest.fixture(autouse=True)
    def _need_pyfixest(self):
        pytest.importorskip("pyfixest")

    def test_two_groups_pvalue(self, df):
        from scipy import stats as sst

        sub = df[df.g.isin(["a", "b"])]
        t = mt.BTable(sub, vars=["x", "y"], group="g")
        assert "p-value" in str(t.df.columns[-1])
        expected = sst.ttest_ind(
            sub.loc[sub.g == "a", "x"], sub.loc[sub.g == "b", "x"]
        ).pvalue
        assert float(t.df.iloc[0, -1]) == pytest.approx(expected, abs=1e-3)
        assert t.df.columns.nlevels == 2

    def test_three_groups_joint(self, df):
        t = mt.BTable(df, vars=["x", "y"], group="g", pdigits=4)
        px, py = (float(v) for v in t.df.iloc[:, -1])
        assert px < 0.001  # x differs strongly in group b
        assert 0 <= py <= 1
        assert len(t.df.iloc[0, -1].split(".")[1]) == 4

    def test_multi_group_columns(self, df):
        t = mt.BTable(df, vars=["x"], group=["g", "h"])
        assert float(t.df.iloc[0, -1]) < 0.001

    def test_byrow_per_block(self, df):
        t = mt.BTable(df, vars=["x", "y"], group="g", byrow="h")
        assert isinstance(t.df.index, pd.MultiIndex)
        pv = t.df.iloc[:, -1]
        assert len(pv) == 4
        assert all(p != "" for p in pv)

    def test_byrow_single_group_blank(self, df):
        df2 = df.copy()
        df2["g2"] = np.where(df2.h == "v", np.tile(["a", "b"], len(df2) // 2), "a")
        t = mt.BTable(df2, vars=["x"], group="g2", byrow="h")
        assert "" in list(t.df.iloc[:, -1])

    def test_robust_and_cluster_notes(self, df):
        t = mt.BTable(df, vars=["x"], group="g", vcov="hetero")
        assert "robust standard errors" in t.notes
        t = mt.BTable(
            df, vars=["x"], group="g", vcov={"CRV1": "h"}, labels={"h": "Hgroup"}
        )
        assert "clustered on hgroup" in t.notes
        t = mt.BTable(df, vars=["x"], group="g", fixed_effects=["h"])
        assert "h fixed effects" in t.notes
        t = mt.BTable(df, vars=["x"], group="g", fixed_effects=["h"], vcov="HC1")
        assert "fixed effects and robust" in t.notes

    def test_default_notes_empty(self, df):
        t = mt.BTable(df, vars=["x"], group="g")
        assert not t.notes

    def test_hide_stats_notes(self, df):
        t = mt.BTable(df, vars=["x"], group="g", hide_stats=True)
        assert "displayed statistics are mean, std. dev." in t.notes.lower()
        assert "p-value" in str(t.df.columns[-1])
        t = mt.BTable(
            df,
            vars=["x"],
            group="g",
            hide_stats=True,
            stats=["count", "mean"],
            counts_row_below=True,
        )
        assert t.notes.endswith("mean.")

    def test_custom_notes(self, df):
        t = mt.BTable(df, vars=["x"], group="g", notes="Custom")
        assert t.notes == "Custom"

    @pytest.mark.parametrize(
        ("kwargs", "match"),
        [
            ({"vars": ["x"], "group": "nope"}, "group must"),
            ({"vars": ["x"], "group": []}, "at least one"),
            ({"vars": ["x"], "group": "g", "byrow": "nope"}, "byrow"),
            ({"vars": ["nope"], "group": "g"}, "not in DataFrame"),
        ],
    )
    def test_errors(self, df, kwargs, match):
        with pytest.raises(ValueError, match=match):
            mt.BTable(df, **kwargs)

    def test_requires_pyfixest(self, df, monkeypatch):
        import maketables.btable as bt

        monkeypatch.setattr(bt, "HAS_PYFIXEST", False)
        with pytest.raises(ImportError, match="pyfixest"):
            mt.BTable(df, vars=["x"], group="g")
