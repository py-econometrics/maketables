"""Tests for embedded line breaks (\\n) in labels, headers, and notes.

Data cells already supported this before this change; these tests cover the
previously-missing positions: row labels, column headers/spanners, and
notes, across the tex, typst, and gt/html backends. Docx already handled
all of these implicitly (python-docx converts embedded newlines on its own),
so it isn't covered here. Captions do not support line breaks - a caption
is a single-line label by design.
"""

import pandas as pd
from helpers import normalize_html

import maketables as mt


class TestLineBreaksTex:
    """Line breaks should render as a real \\\\ inside \\makecell{}."""

    def test_label_linebreak(self, fitted_model, snapshot):
        table = mt.ETable([fitted_model], labels={"x": "Line one\nLine two"})
        assert table.make(type="tex") == snapshot

    def test_header_linebreak(self, fitted_model, snapshot):
        table = mt.ETable([fitted_model], model_heads=["Line one\nLine two"])
        assert table.make(type="tex") == snapshot

    def test_notes_linebreak(self, fitted_model, snapshot):
        table = mt.ETable([fitted_model], notes="Line one\nLine two")
        assert table.make(type="tex") == snapshot

    def test_row_group_name_linebreak(self):
        r"""Row-group header names go through their own code path (formatted
        via group_header_format before being emitted), separate from row
        labels/headers/notes - it must convert \n too, not emit it as a
        literal newline inside \emph{...}, which LaTeX would just treat as
        whitespace.
        """
        idx = pd.MultiIndex.from_tuples(
            [("Group\nBreak", "a"), ("Group\nBreak", "b")]
        )
        table = mt.MTable(pd.DataFrame({"col1": [1, 2]}, index=idx))
        tex = table.make(type="tex")
        assert r"\makecell{\emph{Group\\Break}}" in tex


class TestLineBreaksGt:
    """Line breaks should render as a real <br>, not escaped &lt;br&gt; text."""

    def test_label_linebreak(self, fitted_model, snapshot):
        table = mt.ETable([fitted_model], labels={"x": "Line one\nLine two"})
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_header_linebreak(self, fitted_model, snapshot):
        table = mt.ETable([fitted_model], model_heads=["Line one\nLine two"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_notes_linebreak(self, fitted_model, snapshot):
        table = mt.ETable([fitted_model], notes="Line one\nLine two")
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_special_characters_still_escaped_alongside_linebreak(self, fitted_model):
        """A real <br> must appear, but any other special characters on
        either side of it must still be escaped, not passed through raw.
        """
        table = mt.ETable([fitted_model], notes="A<B\nC>D")
        html = table.make(type="gt").as_raw_html()
        assert "A&lt;B<br>C&gt;D" in html
        assert "<br>" in html

    def test_notes_none_stays_empty(self, fitted_model):
        """notes=None means 'no notes' (DEFAULT_NOTES is "", not None), and
        must render as an empty source note - not the literal text "None".
        """
        table = mt.ETable([fitted_model], notes=None)
        html = table.make(type="gt").as_raw_html()
        assert ">None<" not in html


class TestLineBreaksTypst:
    """Line breaks should render as Typst's native ' \\ ' line-break syntax."""

    def test_label_linebreak(self, fitted_model):
        table = mt.ETable([fitted_model], labels={"x": "Line one\nLine two"})
        typst = table.make(type="typst")
        assert "Line one \\ Line two" in typst

    def test_header_linebreak(self, fitted_model):
        table = mt.ETable([fitted_model], model_heads=["Line one\nLine two"])
        typst = table.make(type="typst")
        assert "Line one \\ Line two" in typst

    def test_notes_linebreak(self, fitted_model):
        table = mt.ETable([fitted_model], notes="Line one\nLine two")
        typst = table.make(type="typst")
        assert "Line one \\ Line two" in typst

    def test_escaping_still_applied_alongside_linebreak(self, fitted_model):
        """Each line must still be escaped individually (e.g. a literal
        underscore), not just naively joined.
        """
        table = mt.ETable([fitted_model], labels={"x": "a_1\nb_2"})
        typst = table.make(type="typst")
        assert r"a\_1 \ b\_2" in typst

    def test_blank_line_between_linebreaks_preserved(self, fitted_model):
        r"""A blank line (two consecutive \n) must produce an extra break,
        not be silently dropped - matching tex (\\\\) and gt (<br><br>).
        """
        table = mt.ETable([fitted_model], notes="Line one\n\nLine two")
        typst = table.make(type="typst")
        assert "Line one \\  \\ Line two" in typst
