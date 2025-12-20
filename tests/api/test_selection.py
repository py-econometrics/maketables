"""Snapshot tests for ETable coefficient selection (keep/drop)."""

import maketables as mt
from helpers import normalize_html


class TestETableCoefSelection:
    """Snapshot tests for keep/drop coefficient filtering."""

    def test_keep_single_coef_html(self, fitted_models, snapshot):
        """Keep only x coefficient."""
        table = mt.ETable(fitted_models, keep=["x"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_keep_single_coef_latex(self, fitted_models, snapshot):
        """Keep only x coefficient."""
        table = mt.ETable(fitted_models, keep=["x"])
        assert table.make(type="tex") == snapshot

    def test_drop_intercept_html(self, fitted_model, snapshot):
        """Drop intercept from table."""
        table = mt.ETable([fitted_model], drop=["Intercept"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_drop_intercept_latex(self, fitted_model, snapshot):
        """Drop intercept from table."""
        table = mt.ETable([fitted_model], drop=["Intercept"])
        assert table.make(type="tex") == snapshot

    def test_keep_with_regex_html(self, fitted_models, snapshot):
        """Keep coefficients using regex pattern."""
        table = mt.ETable(fitted_models, keep=["x", "C\\(group\\)"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_keep_with_regex_latex(self, fitted_models, snapshot):
        """Keep coefficients using regex pattern."""
        table = mt.ETable(fitted_models, keep=["x", "C\\(group\\)"])
        assert table.make(type="tex") == snapshot

    def test_exact_match_html(self, fitted_models, snapshot):
        """Exact match mode (no regex)."""
        table = mt.ETable(fitted_models, keep=["x"], exact_match=True)
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_exact_match_latex(self, fitted_models, snapshot):
        """Exact match mode (no regex)."""
        table = mt.ETable(fitted_models, keep=["x"], exact_match=True)
        assert table.make(type="tex") == snapshot

    def test_keep_reorders_html(self, fitted_models, snapshot):
        """Keep reorders coefficients according to pattern order."""
        table = mt.ETable(fitted_models, keep=["C\\(group\\)", "x", "Intercept"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_keep_reorders_latex(self, fitted_models, snapshot):
        """Keep reorders coefficients according to pattern order."""
        table = mt.ETable(fitted_models, keep=["C\\(group\\)", "x", "Intercept"])
        assert table.make(type="tex") == snapshot
