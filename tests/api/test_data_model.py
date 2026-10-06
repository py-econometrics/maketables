"""Layer 1 tests: the pre-render data model that every output format consumes."""

import pandas as pd
import pytest

import maketables as mt


class TestSampleTableDataModel:
    """The DataFrame each renderer reads, before any format-specific rendering."""

    def test_df_snapshot(self, sample_table, snapshot):
        """Snapshot the table's DataFrame (values, index and column labels)."""
        assert sample_table.df.to_csv().strip() == snapshot

    def test_df_is_dataframe_with_content(self, sample_table):
        assert isinstance(sample_table.df, pd.DataFrame)
        assert not sample_table.df.empty

    def test_row_index_has_at_most_two_levels(self, sample_table):
        assert sample_table.df.index.nlevels <= 2

    def test_render_context_attributes(self, sample_table):
        """Attributes the renderers read are set on every table type."""
        assert isinstance(sample_table.notes, str)
        assert isinstance(sample_table.rgroup_sep, str)
        assert isinstance(sample_table.rgroup_display, bool)

    @pytest.mark.parametrize("output_type", ["gt", "tex", "typst"])
    def test_make_does_not_mutate_df(self, sample_table, output_type):
        """Rendering reads the data model without changing it."""
        before = sample_table.df.copy(deep=True)
        sample_table.make(type=output_type)
        pd.testing.assert_frame_equal(sample_table.df, before)


class TestMergedHeaders:
    """Spanning headers show up as MultiIndex columns in the data model."""

    def test_merged_model_heads_give_multiindex_columns(self, fitted_models):
        table = mt.ETable(
            fitted_models,
            model_heads=[["Panel A", "Panel A"], ["Spec 1", "Spec 2"]],
            head_order="h",
        )
        assert isinstance(table.df.columns, pd.MultiIndex)
        # two header rows plus the model-number row
        assert table.df.columns.nlevels == 3

    def test_grouped_dtable_columns_are_multiindex(self, simple_df):
        table = mt.DTable(simple_df, vars=["x", "y"], bycol=["group"])
        assert isinstance(table.df.columns, pd.MultiIndex)

    def test_plain_dtable_columns_are_flat(self, simple_df):
        table = mt.DTable(simple_df, vars=["x", "y"])
        assert not isinstance(table.df.columns, pd.MultiIndex)


class TestMTableValidation:
    """MTable's constructor validates the DataFrame and stores render context."""

    def test_rejects_non_dataframe(self):
        with pytest.raises(TypeError, match="DataFrame"):
            mt.MTable([[1, 2], [3, 4]])

    def test_rejects_more_than_two_row_index_levels(self):
        index = pd.MultiIndex.from_tuples([("a", "b", "c")])
        with pytest.raises(ValueError, match="at most two levels"):
            mt.MTable(pd.DataFrame({"v": [1]}, index=index))

    def test_stores_render_context(self):
        df = pd.DataFrame({"v": [1.0]}, index=pd.MultiIndex.from_tuples([("g", "r")]))
        table = mt.MTable(
            df,
            notes="n",
            caption="c",
            tab_label="tab:x",
            rgroup_sep="tb",
            rgroup_display=False,
        )
        assert table.df is df
        assert (table.notes, table.caption, table.tab_label) == ("n", "c", "tab:x")
        assert table.rgroup_sep == "tb"
        assert table.rgroup_display is False
