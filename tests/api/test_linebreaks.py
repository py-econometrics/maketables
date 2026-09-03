"""Tests for embedded line breaks (\\n) in labels, headers, captions, and notes.

Data cells already supported this before this change; these tests cover the
previously-missing positions: row labels, column headers/spanners, caption,
and notes, across the tex, typst, and gt/html backends. Docx already handled
all of these implicitly (python-docx converts embedded newlines on its own),
so it isn't covered here.
"""

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

    def test_caption_linebreak(self, fitted_model, snapshot):
        table = mt.ETable([fitted_model], caption="Line one\nLine two")
        assert table.make(type="tex") == snapshot

    def test_notes_linebreak(self, fitted_model, snapshot):
        table = mt.ETable([fitted_model], notes="Line one\nLine two")
        assert table.make(type="tex") == snapshot


class TestLineBreaksGt:
    """Line breaks should render as a real <br>, not escaped &lt;br&gt; text."""

    def test_label_linebreak(self, fitted_model, snapshot):
        table = mt.ETable([fitted_model], labels={"x": "Line one\nLine two"})
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_header_linebreak(self, fitted_model, snapshot):
        table = mt.ETable([fitted_model], model_heads=["Line one\nLine two"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_caption_linebreak(self, fitted_model, snapshot):
        table = mt.ETable([fitted_model], caption="Line one\nLine two")
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_notes_linebreak(self, fitted_model, snapshot):
        table = mt.ETable([fitted_model], notes="Line one\nLine two")
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_special_characters_still_escaped_alongside_linebreak(self, fitted_model):
        """A real <br> must appear, but any other special characters on
        either side of it must still be escaped, not passed through raw.
        """
        table = mt.ETable([fitted_model], caption="A<B\nC>D")
        html = table.make(type="gt").as_raw_html()
        assert "A&lt;B<br>C&gt;D" in html
        assert "<br>" in html


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

    def test_caption_linebreak(self, fitted_model):
        table = mt.ETable([fitted_model], caption="Line one\nLine two")
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
