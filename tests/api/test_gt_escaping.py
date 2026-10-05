r"""Tests for line breaks and HTML escaping in great_tables body cells.

great_tables >= 1.0 HTML-escapes body cells, row labels (stub) and row-group
labels by default, while older versions pass them through raw. These tests
check that "\n" renders as a real <br> and user text is escaped in either
case, so they deliberately avoid snapshots (whose CSS differs between
great_tables versions) and can run against any supported version.
"""

import re

import pandas as pd
import pytest

import maketables as mt


def _gt_html(table):
    return table.make(type="gt").as_raw_html()


def _cells(html):
    return re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", html, re.DOTALL)


@pytest.fixture
def grouped_mtable():
    idx = pd.MultiIndex.from_tuples(
        [("Group\nBreak", "Row\nBreak"), ("Group\nBreak", "a < b & c")]
    )
    return mt.MTable(pd.DataFrame({"col1": ["1\n(2)", "x < y"]}, index=idx))


class TestEtableCells:
    """Coefficient cells and variable labels in ETable."""

    def test_coef_se_cell_has_real_linebreak(self, fitted_model):
        html = _gt_html(mt.ETable([fitted_model]))
        coef_cells = [c for c in _cells(html) if "(" in c and "<br>" in c]
        assert coef_cells, "no coefficient cell with a real <br> line break"
        assert "&lt;br&gt;" not in html

    def test_label_with_special_chars_is_escaped(self, fitted_model):
        table = mt.ETable([fitted_model], labels={"x": "a < b & c\nline two"})
        html = _gt_html(table)
        assert "a &lt; b &amp; c<br>line two" in html
        assert "a < b & c" not in html

    def test_label_with_markup_is_not_rendered(self, fitted_model):
        table = mt.ETable([fitted_model], labels={"x": "<b>bold</b>"})
        html = _gt_html(table)
        assert "&lt;b&gt;bold&lt;/b&gt;" in html
        assert "<b>bold</b>" not in html


class TestHeaders:
    """Model headers, depvar labels and spanners, which GT always escapes."""

    @staticmethod
    def _visible_text(html):
        # GT derives spanner id="..." attributes from the label text, where an
        # escaped &lt;br&gt; is harmless; only check what is actually shown.
        return re.sub(r"<[^>]*>", "|", html)

    @pytest.mark.parametrize(
        ("kwargs", "expected"),
        [
            ({"model_heads": ["Head one\nHead two"]}, "Head one<br>Head two"),
            ({"model_heads": [["Top one\nTop two"], ["a\nb"]]}, "Top one<br>Top two"),
            ({"model_heads": [["Top"], ["a\nb"]]}, "a<br>b"),
            ({"labels": {"y": "Dep one\nDep two"}}, "Dep one<br>Dep two"),
            ({"model_heads": ["a < b\nc"]}, "a &lt; b<br>c"),
        ],
    )
    def test_etable_header_linebreak(self, fitted_model, kwargs, expected):
        html = _gt_html(mt.ETable([fitted_model], **kwargs))
        assert expected in html
        assert "&lt;br&gt;" not in self._visible_text(html)

    def test_dtable_bycol_header_linebreak(self, simple_df):
        df = simple_df.assign(group=simple_df["group"].map({"A": "Col\nA", "B": "B"}))
        html = _gt_html(mt.DTable(df, vars=["x"], bycol=["group"]))
        assert "Col<br>A" in html
        assert "&lt;br&gt;" not in self._visible_text(html)


class TestMtableLabels:
    """Body cells, row labels and row-group labels in MTable."""

    def test_row_label_linebreak(self, grouped_mtable):
        html = _gt_html(grouped_mtable)
        assert "Row<br>Break" in html
        assert "&lt;br&gt;" not in html

    def test_row_group_label_linebreak(self, grouped_mtable):
        html = _gt_html(grouped_mtable)
        assert "Group<br>Break" in html

    def test_body_cell_linebreak_and_escaping(self, grouped_mtable):
        html = _gt_html(grouped_mtable)
        assert "1<br>(2)" in html
        assert "x &lt; y" in html

    def test_row_label_special_chars_escaped(self, grouped_mtable):
        html = _gt_html(grouped_mtable)
        assert "a &lt; b &amp; c" in html
        assert "a < b & c" not in html

    def test_non_string_cells_unchanged(self):
        df = pd.DataFrame({"i": [1, 2], "f": [1.5, float("nan")]}, index=["r1", "r2"])
        cells = _cells(_gt_html(mt.MTable(df)))
        assert "1" in cells
        assert "1.5" in cells
        assert "nan" not in cells


class TestDtableLabels:
    """Variable labels and byrow group labels in DTable."""

    def test_dtable_row_label_and_group_linebreak(self, simple_df):
        df = simple_df.assign(group=simple_df["group"].map({"A": "A\nx", "B": "B<y"}))
        table = mt.DTable(df, vars=["x"], byrow="group", labels={"x": "Var\nX"})
        html = _gt_html(table)
        assert "Var<br>X" in html
        assert "A<br>x" in html
        assert "B&lt;y" in html
        assert "&lt;br&gt;" not in html


class TestOtherOutputsUnaffected:
    """Non-HTML outputs must not pick up <br> tags or HTML escaping."""

    @pytest.fixture
    def table(self, fitted_model):
        return mt.ETable([fitted_model], labels={"x": "a < b & c\nline two"})

    def test_tex_has_no_html(self, table):
        tex = table.make(type="tex")
        assert "<br>" not in tex
        assert "&lt;" not in tex

    def test_typst_has_no_html(self, table):
        typst = table.make(type="typst")
        assert "<br>" not in typst
        assert "&lt;" not in typst

    def test_df_has_no_html_after_gt_render(self, table):
        _gt_html(table)
        text = table.df.to_string() + " ".join(map(str, table.df.index))
        assert "<br>" not in text
        assert "&lt;" not in text
        assert "&amp;" not in text

    def test_docx_has_no_html(self, table):
        doc = table.make(type="docx")
        text = "\n".join(
            cell.text for t in doc.tables for row in t.rows for cell in row.cells
        )
        assert "a < b & c" in text
        assert "<br>" not in text
        assert "&lt;" not in text
