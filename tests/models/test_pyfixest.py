"""Base snapshot tests for pyfixest models."""

import pandas as pd
import pytest
from helpers import OUTPUT_TYPES, render_table

import maketables as mt


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
        import numpy as np
        import pyfixest as pf

        np.random.seed(42)
        df = pf.get_data(N=100, seed=0, model="Feols")

        # Create list of FixestMulti objects (stepwise notation in each formula)
        fmls = ["Y ~ X1 | sw0(f1, f2)", "Y ~ X2 | sw0(f1, f2)"]
        models = [pf.feols(fml=fml, data=df) for fml in fmls]

        # Should expand FixestMulti objects and create a table
        table = mt.ETable(models)
        assert render_table(table, output_type) == snapshot


class TestFixedEffectRows:
    """Fixed-effect presence rows for multi-FE pyfixest models."""

    @pytest.fixture
    def fe_df(self):
        import numpy as np

        rng = np.random.default_rng(0)
        n = 200
        return pd.DataFrame(
            {
                "y": rng.normal(size=n),
                "x": rng.normal(size=n),
                "f": rng.integers(0, 5, n),
                "g": rng.integers(0, 3, n),
            }
        )

    def _fe_rows(self, table):
        fe = table.df.loc["fe"]
        return {label: list(row) for label, row in fe.iterrows()}

    @pytest.mark.parametrize("fml", ["y ~ x | f + g", "y ~ x | f+g"])
    def test_both_fixed_effects_marked(self, fe_df, fml):
        import pyfixest as pf

        table = mt.ETable([pf.feols("y ~ x | f", fe_df), pf.feols(fml, fe_df)])
        assert self._fe_rows(table) == {"f": ["x", "x"], "g": ["-", "x"]}

    def test_cumulative_stepwise_fixed_effects(self, fe_df):
        import pyfixest as pf

        table = mt.ETable(pf.feols("y ~ x | csw0(f, g)", fe_df))
        assert self._fe_rows(table) == {"f": ["-", "x", "x"], "g": ["-", "-", "x"]}

    def test_interacted_fixed_effect_is_one_row(self, fe_df):
        import pyfixest as pf

        table = mt.ETable(
            [pf.feols("y ~ x | f^g", fe_df), pf.feols("y ~ x | f + g", fe_df)]
        )
        assert self._fe_rows(table) == {
            "f": ["-", "x"],
            "f^g": ["x", "-"],
            "g": ["-", "x"],
        }
