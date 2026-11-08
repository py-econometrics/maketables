"""Tests for ETable's flat and multi-level model_heads."""

import pandas as pd
import pytest
from helpers import normalize_html

import maketables as mt
from maketables.extractors import _EXTRACTOR_REGISTRY, get_extractor, register_extractor


class TestFlatModelHeads:
    """The original single-row form of model_heads keeps working."""

    def test_flat_model_heads_columns(self, fitted_models):
        """A flat list becomes a single header row, in order."""
        table = mt.ETable(fitted_models, model_heads=["USA", "UK"], head_order="h")
        assert list(table.df.columns.get_level_values(0)) == ["USA", "UK"]

    def test_default_head_order_puts_depvar_before_head(self, fitted_models):
        """Default head_order='dh' stacks dep var above the head row."""
        table = mt.ETable(fitted_models, model_heads=["USA", "UK"])
        cols = table.df.columns
        assert list(cols.get_level_values(0)) == ["y", "y"]
        assert list(cols.get_level_values(1)) == ["USA", "UK"]

    def test_flat_model_heads_wrong_length_raises(self, fitted_models):
        """A flat model_heads must have one entry per model."""
        with pytest.raises(ValueError, match="one entry per model"):
            mt.ETable(fitted_models, model_heads=["USA"])

    def test_flat_model_heads_html(self, fitted_models, snapshot):
        """Flat model_heads render as a single spanner row in HTML."""
        table = mt.ETable(fitted_models, model_heads=["USA", "UK"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_flat_model_heads_latex(self, fitted_models, snapshot):
        """Flat model_heads render as a single header row in LaTeX."""
        table = mt.ETable(fitted_models, model_heads=["USA", "UK"])
        assert table.make(type="tex") == snapshot


class TestMultiLevelModelHeads:
    """model_heads accepts a list of levels to stack multiple header rows."""

    def test_two_levels_stacked_top_to_bottom(self, fitted_models):
        """Levels appear in the order given, each aligned to the models."""
        table = mt.ETable(
            fitted_models,
            model_heads=[["USA", "USA"], ["OLS", "IV"]],
            head_order="h",
        )
        cols = table.df.columns
        assert isinstance(cols, pd.MultiIndex)
        assert list(cols.get_level_values(0)) == ["USA", "USA"]
        assert list(cols.get_level_values(1)) == ["OLS", "IV"]

    def test_tuples_are_accepted_like_lists(self, fitted_models):
        """Tuples of levels/entries work the same as lists."""
        table = mt.ETable(
            fitted_models,
            model_heads=(("USA", "USA"), ("OLS", "IV")),
            head_order="h",
        )
        cols = table.df.columns
        assert list(cols.get_level_values(0)) == ["USA", "USA"]
        assert list(cols.get_level_values(1)) == ["OLS", "IV"]

    def test_partial_blanks_within_a_level_are_kept_for_spanners(self, fitted_models):
        """A level blank for *some* models is kept (used to merge spanner cells)."""
        table = mt.ETable(
            fitted_models,
            model_heads=[["USA", ""], ["OLS", "IV"]],
            head_order="h",
        )
        cols = table.df.columns
        assert list(cols.get_level_values(0)) == ["USA", ""]

    def test_fully_blank_level_is_dropped(self, fitted_models):
        """A level blank for every model is omitted entirely."""
        with_blank = mt.ETable(
            fitted_models,
            model_heads=[["", ""], ["OLS", "IV"]],
            head_order="h",
        )
        without_blank = mt.ETable(
            fitted_models, model_heads=["OLS", "IV"], head_order="h"
        )
        # A level that is blank for every model carries no information and
        # must not show up as an extra (empty) header row.
        assert list(with_blank.df.columns) == list(without_blank.df.columns)

    def test_head_order_h_only_keeps_all_levels(self, fitted_models):
        """head_order='h' inserts every model_heads level, plus model numbers."""
        table = mt.ETable(
            fitted_models,
            model_heads=[["USA", "USA"], ["OLS", "IV"]],
            head_order="h",
        )
        cols = table.df.columns
        assert isinstance(cols, pd.MultiIndex)
        # both head levels plus the trailing model-number level
        assert cols.nlevels == 3
        assert list(cols.get_level_values(0)) == ["USA", "USA"]
        assert list(cols.get_level_values(1)) == ["OLS", "IV"]
        assert list(cols.get_level_values(2)) == ["(1)", "(2)"]

    def test_head_order_empty_shows_only_model_numbers(self, fitted_models):
        """head_order='' ignores model_heads entirely."""
        table = mt.ETable(
            fitted_models,
            model_heads=[["USA", "USA"], ["OLS", "IV"]],
            head_order="",
        )
        assert list(table.df.columns) == ["(1)", "(2)"]

    def test_nested_level_wrong_length_raises(self, fitted_models):
        """Every level in the nested form must align with the models."""
        with pytest.raises(ValueError, match="one entry per model"):
            mt.ETable(fitted_models, model_heads=[["USA", "USA"], ["OLS"]])

    def test_nested_level_plain_string_raises_instead_of_exploding(self, fitted_models):
        """A plain string level is rejected instead of exploding into chars."""
        with pytest.raises(TypeError, match="list or tuple"):
            mt.ETable(fitted_models, model_heads=[["USA", "USA"], "OLS"])

    def test_multi_level_html(self, fitted_models, snapshot):
        """Multi-level model_heads render as stacked spanner rows in HTML."""
        table = mt.ETable(
            fitted_models,
            model_heads=[["USA", "USA"], ["OLS", "IV"]],
        )
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_multi_level_latex(self, fitted_models, snapshot):
        """Multi-level model_heads render as stacked header rows in LaTeX."""
        table = mt.ETable(
            fitted_models,
            model_heads=[["USA", "USA"], ["OLS", "IV"]],
        )
        assert table.make(type="tex") == snapshot


class TestSampleSplitExtractorHardening:
    """Extractors that predate sample_split() must not crash ETable()."""

    def test_extractor_without_sample_split_degrades_gracefully(self, fitted_model):
        """A third-party extractor lacking sample_split() falls back to None."""
        real_extractor = get_extractor(fitted_model)

        class LegacyExtractor:
            """Mimics a third-party extractor written before sample_split() existed."""

            def can_handle(self, model):
                return model is fitted_model

            def coef_table(self, model):
                return real_extractor.coef_table(model)

            def depvar(self, model):
                return real_extractor.depvar(model)

            def stat(self, model, key):
                return real_extractor.stat(model, key)

            def fixef_string(self, model):
                return real_extractor.fixef_string(model)

            def vcov_info(self, model):
                return real_extractor.vcov_info(model)

            def var_labels(self, model):
                return None

            def supported_stats(self, model):
                return real_extractor.supported_stats(model)

            def default_stat_keys(self, model):
                return None

        legacy = LegacyExtractor()
        assert not hasattr(legacy, "sample_split")

        register_extractor(legacy)
        try:
            table = mt.ETable([fitted_model])
        finally:
            _EXTRACTOR_REGISTRY.remove(legacy)

        # No sample-split header should be inferred for an extractor that
        # cannot report one: only the depvar/model-number levels appear.
        assert list(table.df.columns) == [("y", "(1)")]


class TestNestedSpannerBoundaries:
    """A lower header level never merges across a higher-level boundary."""

    @pytest.fixture
    def crossing_table(self):
        cols = pd.MultiIndex.from_tuples(
            [
                ("US", "OLS", "(1)"),
                ("US", "IV", "(2)"),
                ("UK", "IV", "(3)"),
                ("UK", "OLS", "(4)"),
            ]
        )
        return mt.MTable(
            pd.DataFrame([["1", "2", "3", "4"]], index=["x"], columns=cols)
        )

    @staticmethod
    def _docx_spans(row):
        spans = []
        for cell in row.cells[1:]:
            if spans and cell._tc is spans[-1][0]:  # noqa: SLF001
                spans[-1][2] += 1
            else:
                spans.append([cell._tc, cell.text, 1])  # noqa: SLF001
        return [(text, n) for _, text, n in spans]

    def test_latex(self, crossing_table):
        lines = crossing_table.make(type="tex").splitlines()
        assert (
            " & \\multicolumn{1}{c}{OLS} & \\multicolumn{1}{c}{IV}"
            " & \\multicolumn{1}{c}{IV} & \\multicolumn{1}{c}{OLS} \\\\"
        ) in lines
        assert (
            "\\cmidrule(lr){2-2} \\cmidrule(lr){3-3} "
            "\\cmidrule(lr){4-4} \\cmidrule(lr){5-5}"
        ) in lines

    def test_typst(self, crossing_table):
        typst = crossing_table.make(type="typst")
        assert "[#table.cell(colspan: 2)[IV]]" not in typst
        assert typst.count("[#table.cell(colspan: 1)[IV]]") == 2
        assert "column-gutter: (0em, 0.5em, 0.5em, 0.5em)," in typst

    def test_gt(self, crossing_table):
        import re

        html = crossing_table.make(type="gt").as_raw_html()
        spans = re.findall(
            r'colspan="(\d)"[^>]*>\s*<span class="gt_column_spanner">(\w+)<', html
        )
        assert spans == [
            ("2", "US"),
            ("2", "UK"),
            ("1", "OLS"),
            ("1", "IV"),
            ("1", "IV"),
            ("1", "OLS"),
        ]

    def test_docx(self, crossing_table):
        rows = crossing_table.make(type="docx").tables[0].rows
        assert self._docx_spans(rows[0]) == [("US", 2), ("UK", 2)]
        assert self._docx_spans(rows[1]) == [
            ("OLS", 1),
            ("IV", 1),
            ("IV", 1),
            ("OLS", 1),
        ]

    def test_run_inside_one_group_still_merges(self):
        cols = pd.MultiIndex.from_tuples(
            [("US", "IV", "(1)"), ("US", "IV", "(2)"), ("UK", "IV", "(3)")]
        )
        table = mt.MTable(pd.DataFrame([["1", "2", "3"]], index=["x"], columns=cols))
        tex = table.make(type="tex")
        assert " & \\multicolumn{2}{c}{IV} & \\multicolumn{1}{c}{IV} \\\\" in tex
        assert self._docx_spans(table.make(type="docx").tables[0].rows[1]) == [
            ("IV", 2),
            ("IV", 1),
        ]

    def test_etable_model_heads(self, fitted_models):
        table = mt.ETable(
            fitted_models * 2,
            model_heads=[["US", "US", "UK", "UK"], ["OLS", "IV", "IV", "OLS"]],
        )
        tex = table.make(type="tex")
        assert "\\multicolumn{2}{c}{IV}" not in tex
        assert tex.count("\\multicolumn{1}{c}{IV}") == 2
