"""Base snapshot tests for pyfixest models."""

from helpers import normalize_html

import maketables as mt


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

    def test_multi_fixest_with_stepwise_html(self, snapshot):
        """Multiple pyfixest formulas with stepwise notation (FixestMulti objects)."""
        import numpy as np
        import pyfixest as pf

        np.random.seed(42)
        df = pf.get_data(N=100, seed=0, model="Feols")

        # Create list of FixestMulti objects (stepwise notation in each formula)
        fmls = ["Y ~ X1 | sw0(f1, f2)", "Y ~ X2 | sw0(f1, f2)"]
        models = [pf.feols(fml=fml, data=df) for fml in fmls]

        # Should expand FixestMulti objects and create a table
        table = mt.ETable(models)
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_multi_fixest_with_stepwise_latex(self, snapshot):
        """Multiple pyfixest formulas with stepwise notation (FixestMulti objects)."""
        import numpy as np
        import pyfixest as pf

        np.random.seed(42)
        df = pf.get_data(N=100, seed=0, model="Feols")

        # Create list of FixestMulti objects (stepwise notation in each formula)
        fmls = ["Y ~ X1 | sw0(f1, f2)", "Y ~ X2 | sw0(f1, f2)"]
        models = [pf.feols(fml=fml, data=df) for fml in fmls]

        # Should expand FixestMulti objects and create a table
        table = mt.ETable(models)
        assert table.make(type="tex") == snapshot
