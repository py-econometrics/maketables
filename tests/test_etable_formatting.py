"""Snapshot tests for ETable coefficient formatting."""

import re

import maketables as mt


def normalize_html(html: str) -> str:
    """Normalize HTML output by replacing random IDs with a stable placeholder."""
    normalized = re.sub(r'id="([a-z]{10})"', 'id="STABLE_ID"', html)
    normalized = re.sub(r"#[a-z]{10}", "#STABLE_ID", normalized)
    return normalized


class TestETableCoefFormat:
    """Snapshot tests for coef_fmt variations."""

    def test_coef_fmt_default_html(self, fitted_model, snapshot):
        """Default coefficient format (b with SE)."""
        table = mt.ETable([fitted_model])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_coef_fmt_default_latex(self, fitted_model, snapshot):
        """Default coefficient format (b with SE)."""
        table = mt.ETable([fitted_model])
        assert table.make(type="tex") == snapshot

    def test_coef_fmt_with_tstat_html(self, fitted_model, snapshot):
        """Coefficient with t-statistic in brackets."""
        table = mt.ETable([fitted_model], coef_fmt="b:.3f \n [t:.2f]")
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_coef_fmt_with_tstat_latex(self, fitted_model, snapshot):
        """Coefficient with t-statistic in brackets."""
        table = mt.ETable([fitted_model], coef_fmt="b:.3f \n [t:.2f]")
        assert table.make(type="tex") == snapshot

    def test_coef_fmt_with_pvalue_html(self, fitted_model, snapshot):
        """Coefficient with p-value."""
        table = mt.ETable([fitted_model], coef_fmt="b:.3f \n (p:.4f)")
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_coef_fmt_with_pvalue_latex(self, fitted_model, snapshot):
        """Coefficient with p-value."""
        table = mt.ETable([fitted_model], coef_fmt="b:.3f \n (p:.4f)")
        assert table.make(type="tex") == snapshot

    def test_coef_fmt_all_stats_html(self, fitted_model, snapshot):
        """Coefficient with SE and t-statistic."""
        table = mt.ETable([fitted_model], coef_fmt="b:.3f \n (se:.3f) \n [t:.2f]")
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_coef_fmt_all_stats_latex(self, fitted_model, snapshot):
        """Coefficient with SE and t-statistic."""
        table = mt.ETable([fitted_model], coef_fmt="b:.3f \n (se:.3f) \n [t:.2f]")
        assert table.make(type="tex") == snapshot

    def test_coef_fmt_different_decimals_html(self, fitted_model, snapshot):
        """Different decimal places for coefficient and SE."""
        table = mt.ETable([fitted_model], coef_fmt="b:.4f \n (se:.2f)")
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_coef_fmt_different_decimals_latex(self, fitted_model, snapshot):
        """Different decimal places for coefficient and SE."""
        table = mt.ETable([fitted_model], coef_fmt="b:.4f \n (se:.2f)")
        assert table.make(type="tex") == snapshot
