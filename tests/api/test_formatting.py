"""Snapshot tests for ETable coefficient formatting."""

import pytest
from helpers import OUTPUT_TYPES, render_table

import maketables as mt
from maketables.etable import _parse_coef_fmt
from maketables.extractors import get_extractor


class TestETableCoefFormat:
    """Snapshot tests for coef_fmt variations."""

    @pytest.mark.parametrize("output_type", OUTPUT_TYPES)
    @pytest.mark.parametrize(
        "coef_fmt",
        [
            pytest.param(None, id="default"),
            pytest.param("b:.3f \n [t:.2f]", id="with_tstat"),
            pytest.param("b:.3f \n (p:.4f)", id="with_pvalue"),
            pytest.param("b:.3f \n (se:.3f) \n [t:.2f]", id="all_stats"),
            pytest.param("b:.4f \n (se:.2f)", id="different_decimals"),
        ],
    )
    def test_coef_fmt(self, fitted_model, snapshot, coef_fmt, output_type):
        """Coefficient format variations."""
        kwargs = {} if coef_fmt is None else {"coef_fmt": coef_fmt}
        table = mt.ETable([fitted_model], **kwargs)
        assert render_table(table, output_type) == snapshot


class TestCoefFmtParsing:
    """Tokens are whole words, and a format spec ends where it stops being valid."""

    CI_COLUMNS = frozenset({"ci95l", "ci95u"})

    @staticmethod
    def parse(coef_fmt, columns=frozenset()):
        return _parse_coef_fmt(coef_fmt, {}, set(columns))

    @pytest.mark.parametrize(
        ("coef_fmt", "title"),
        [
            pytest.param(
                "b (joint t:.2f)", "Coefficient (joint t-stats)", id="t-in-word"
            ),
            pytest.param("b (pages)", "Coefficient (pages)", id="p-starts-word"),
            pytest.param(
                "b (best se)", "Coefficient (best Std. Error)", id="se-in-word"
            ),
            pytest.param("b, t2", "Coefficient, t2", id="token-then-digit"),
        ],
    )
    def test_tokens_inside_words_are_literal(self, coef_fmt, title):
        """A token glued to letters, digits or '_' is plain text."""
        assert self.parse(coef_fmt)[1] == title

    @pytest.mark.parametrize(
        ("coef_fmt", "formats", "title"),
        [
            pytest.param(
                "{ci95l:.3f, ci95u:.3f}",
                [".3f", ".3f"],
                "{95% CI Lower, 95% CI Upper}",
                id="braces",
            ),
            pytest.param("<b:.2f>", [".2f"], "<Coefficient>", id="angle-brackets"),
            pytest.param(
                "b:.4f; se:.2f",
                [".4f", ".2f"],
                "Coefficient; Std. Error",
                id="semicolon",
            ),
        ],
    )
    def test_format_spec_stops_before_literal(self, coef_fmt, formats, title):
        """Text after a valid spec is kept as a literal, not folded into the spec."""
        elements, parsed_title = self.parse(coef_fmt, self.CI_COLUMNS)
        assert [e["format"] for e in elements if e["format"] is not None] == formats
        assert parsed_title == title

    @pytest.mark.parametrize(
        ("coef_fmt", "token", "spec", "stars"),
        [
            pytest.param("b:>8.2f", "b", ">8.2f", False, id="align"),
            pytest.param("b:,.0f", "b", ",.0f", False, id="thousands"),
            pytest.param("b:d", "b", "d", False, id="integer"),
            pytest.param("b:.3f*", "b", ".3f", True, id="stars"),
            pytest.param("t:*", "t", "", True, id="stars-no-spec"),
        ],
    )
    def test_valid_specs_unchanged(self, coef_fmt, token, spec, stars):
        """Specs that worked before parse exactly as before."""
        first = self.parse(coef_fmt)[0][0]
        assert (first["token"], first["format"], first["add_stars"]) == (
            token,
            spec,
            stars,
        )

    def test_escaped_newline_separates_tokens(self):
        r"""The two-character '\n' escape still separates tokens: 'b\nse'."""
        tokens = [e["token"] for e in self.parse("b\\nse")[0]]
        assert tokens == ["b", "\n", "se"]

    def test_rendered_braces_and_precision(self, fitted_model):
        """The closing brace and the requested precision both reach the table."""
        se = get_extractor(fitted_model).coef_table(fitted_model)["se"].iloc[0]
        html = mt.ETable([fitted_model], coef_fmt="b:.3f {se:.5f}").make("html")
        assert f"{{{se:.5f}}}" in html

    def test_rendered_word_keeps_letters(self, fitted_model):
        """Letters of a literal word stay letters in the cell, not statistics."""
        tstat = get_extractor(fitted_model).coef_table(fitted_model)["t"].iloc[0]
        html = mt.ETable([fitted_model], coef_fmt="b:.3f (joint t:.2f)").make("html")
        assert f"(joint {tstat:.2f})" in html
