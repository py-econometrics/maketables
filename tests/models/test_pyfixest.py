"""Base snapshot tests for pyfixest models."""

import maketables as mt
from helpers import normalize_html


class TestPyfixest:
    """Base tests for pyfixest model extraction."""

    def test_single_model_html(self, fitted_model, snapshot):
        """Single pyfixest model HTML output."""
        table = mt.ETable([fitted_model])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_single_model_latex(self, fitted_model, snapshot):
        """Single pyfixest model LaTeX output."""
        table = mt.ETable([fitted_model])
        assert table.make(type="tex") == snapshot

    def test_multi_model_html(self, fitted_models, snapshot):
        """Multiple pyfixest models HTML output."""
        table = mt.ETable(fitted_models)
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_multi_model_latex(self, fitted_models, snapshot):
        """Multiple pyfixest models LaTeX output."""
        table = mt.ETable(fitted_models)
        assert table.make(type="tex") == snapshot

    def test_fixed_effects_html(self, fitted_model_fe, snapshot):
        """Pyfixest model with fixed effects HTML output."""
        table = mt.ETable([fitted_model_fe])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_fixed_effects_latex(self, fitted_model_fe, snapshot):
        """Pyfixest model with fixed effects LaTeX output."""
        table = mt.ETable([fitted_model_fe])
        assert table.make(type="tex") == snapshot
