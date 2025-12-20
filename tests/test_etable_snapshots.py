"""Snapshot tests for ETable (regression tables)."""

import re

import maketables as mt


def normalize_html(html: str) -> str:
    """Normalize HTML output by replacing random IDs with a stable placeholder."""
    # Great Tables generates random 10-char IDs like "pndhlhgcwx"
    # Replace both the id attribute and CSS selectors using that ID
    normalized = re.sub(r'id="([a-z]{10})"', 'id="STABLE_ID"', html)
    normalized = re.sub(r"#[a-z]{10}", "#STABLE_ID", normalized)
    return normalized


class TestETableSnapshots:
    """Snapshot tests for ETable output formats."""

    def test_single_model_html(self, fitted_model, snapshot):
        """Single model ETable HTML output."""
        table = mt.ETable([fitted_model])
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_single_model_latex(self, fitted_model, snapshot):
        """Single model ETable LaTeX output."""
        table = mt.ETable([fitted_model])
        latex = table.make(type="tex")
        assert latex == snapshot

    def test_multi_model_html(self, fitted_models, snapshot):
        """Multi-model ETable HTML output."""
        table = mt.ETable(fitted_models)
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_multi_model_latex(self, fitted_models, snapshot):
        """Multi-model ETable LaTeX output."""
        table = mt.ETable(fitted_models)
        latex = table.make(type="tex")
        assert latex == snapshot

    def test_fixed_effects_html(self, fitted_model_fe, snapshot):
        """Model with fixed effects HTML output."""
        table = mt.ETable([fitted_model_fe])
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_fixed_effects_latex(self, fitted_model_fe, snapshot):
        """Model with fixed effects LaTeX output."""
        table = mt.ETable([fitted_model_fe])
        latex = table.make(type="tex")
        assert latex == snapshot
