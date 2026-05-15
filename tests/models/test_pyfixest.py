"""Base snapshot tests for pyfixest models."""

import maketables as mt
import pytest
from helpers import OUTPUT_TYPES, render_table


class TestPyfixest:
    """Base tests for pyfixest model extraction."""

    @pytest.mark.parametrize("output_type", OUTPUT_TYPES)
    @pytest.mark.parametrize(
        "model_fixture",
        [
            pytest.param("fitted_model", id="single_model"),
            pytest.param("fitted_models", id="multi_model"),
            pytest.param("fitted_model_fe", id="fixed_effects"),
        ],
    )
    def test_model(self, request, snapshot, model_fixture, output_type):
        """Pyfixest model output."""
        models = request.getfixturevalue(model_fixture)
        if not isinstance(models, list):
            models = [models]

        table = mt.ETable(models)
        assert render_table(table, output_type) == snapshot

    @pytest.mark.parametrize("output_type", OUTPUT_TYPES)
    def test_multi_fixest_with_stepwise(self, snapshot, output_type):
        """Multiple pyfixest formulas with stepwise notation."""
        import pyfixest as pf
        import numpy as np

        np.random.seed(42)
        df = pf.get_data(N=100, seed=0, model="Feols")

        # Create list of FixestMulti objects (stepwise notation in each formula)
        fmls = ['Y ~ X1 | sw0(f1, f2)', 'Y ~ X2 | sw0(f1, f2)']
        models = [pf.feols(fml=fml, data=df) for fml in fmls]

        # Should expand FixestMulti objects and create a table
        table = mt.ETable(models)
        assert render_table(table, output_type) == snapshot
