"""Base snapshot tests for linearmodels models."""

import pytest
from helpers import OUTPUT_TYPES, render_table

import maketables as mt


class TestLinearmodels:
    """Base tests for linearmodels model extraction."""

    @pytest.mark.parametrize("output_type", OUTPUT_TYPES)
    @pytest.mark.parametrize(
        "model_fixture",
        [
            pytest.param("linearmodels_panelols", id="panelols"),
            pytest.param("linearmodels_pooledols", id="pooledols"),
            pytest.param("linearmodels_absorbingls", id="absorbingls"),
            pytest.param("linearmodels_iv2sls", id="iv2sls"),
        ],
    )
    def test_model(self, request, snapshot, model_fixture, output_type):
        """Linearmodels model output."""
        model = request.getfixturevalue(model_fixture)
        table = mt.ETable([model])
        assert render_table(table, output_type) == snapshot
