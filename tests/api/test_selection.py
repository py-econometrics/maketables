"""Snapshot tests for ETable coefficient selection (keep/drop)."""

import pytest
from helpers import OUTPUT_TYPES, render_table

import maketables as mt


class TestETableCoefSelection:
    """Snapshot tests for keep/drop coefficient filtering."""

    @pytest.mark.parametrize("output_type", OUTPUT_TYPES)
    @pytest.mark.parametrize(
        "model_fixture, table_kwargs",
        [
            pytest.param("fitted_models", {"keep": ["x"]}, id="keep_single_coef"),
            pytest.param("fitted_model", {"drop": ["Intercept"]}, id="drop_intercept"),
            pytest.param(
                "fitted_models",
                {"keep": ["x", "C\\(group\\)"]},
                id="keep_with_regex",
            ),
            pytest.param(
                "fitted_models",
                {"keep": ["x"], "exact_match": True},
                id="exact_match",
            ),
            pytest.param(
                "fitted_models",
                {"keep": ["C\\(group\\)", "x", "Intercept"]},
                id="keep_reorders",
            ),
        ],
    )
    def test_coef_selection(
        self,
        request,
        snapshot,
        model_fixture,
        table_kwargs,
        output_type,
    ):
        """Coefficient selection variations."""
        models = request.getfixturevalue(model_fixture)
        if not isinstance(models, list):
            models = [models]

        table = mt.ETable(models, **table_kwargs)
        assert render_table(table, output_type) == snapshot
