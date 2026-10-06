"""Base snapshot tests for statsmodels models."""

import pytest
from helpers import OUTPUT_TYPES, render_table

import maketables as mt


class TestStatsmodels:
    """Base tests for statsmodels model extraction."""

    @pytest.mark.parametrize("output_type", OUTPUT_TYPES)
    @pytest.mark.parametrize(
        "model_fixture",
        [
            pytest.param("statsmodels_ols", id="ols"),
            pytest.param("statsmodels_logit", id="logit"),
            pytest.param("statsmodels_probit", id="probit"),
        ],
    )
    def test_model(self, request, snapshot, model_fixture, output_type):
        """Statsmodels model output."""
        model = request.getfixturevalue(model_fixture)
        table = mt.ETable([model])
        assert render_table(table, output_type) == snapshot
