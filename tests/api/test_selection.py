"""Snapshot tests for ETable coefficient selection (keep/drop)."""

import pytest
from helpers import OUTPUT_TYPES, render_table

import maketables as mt


class TestETableCoefSelection:
    """Snapshot tests for keep/drop coefficient filtering."""

    @pytest.mark.parametrize("output_type", OUTPUT_TYPES)
    @pytest.mark.parametrize(
        ("model_fixture", "table_kwargs"),
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


@pytest.fixture
def two_regressor_model(simple_df):
    import pyfixest as pf

    df = simple_df.assign(x2=simple_df["y"] - simple_df["x"])
    return pf.feols("y ~ x + x2", data=df)


@pytest.mark.parametrize(
    ("table_kwargs", "expected_rows"),
    [
        # Intercept named by the user: its position is honored.
        ({"order": ["Intercept", "x2", "x"]}, ["Intercept", "x2", "x"]),
        ({"order": ["x2", "Intercept"]}, ["x2", "Intercept", "x"]),
        ({"keep": ["Intercept", "^x$"]}, ["Intercept", "x"]),
        ({"keep": ["Intercept", "x"], "exact_match": True}, ["Intercept", "x"]),
        # Intercept not named: it still goes last.
        ({}, ["x", "x2", "Intercept"]),
        ({"order": ["x2"]}, ["x2", "x", "Intercept"]),
        ({"keep": ".*"}, ["x", "x2", "Intercept"]),
    ],
)
def test_intercept_position(two_regressor_model, table_kwargs, expected_rows):
    table = mt.ETable(two_regressor_model, labels={}, **table_kwargs)
    assert table.df.loc["coef"].index.tolist() == expected_rows
