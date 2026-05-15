"""Snapshot tests for ETable coefficient formatting."""

import maketables as mt
import pytest
from helpers import OUTPUT_TYPES, render_table


class TestETableCoefFormat:
    """Snapshot tests for coef_fmt variations."""

    @pytest.mark.parametrize("output_type", OUTPUT_TYPES)
    @pytest.mark.parametrize(
        "coef_fmt",
        [
            pytest.param(None, id="default"),
            pytest.param("b:.3f \n [t:.2f]", id="with_tstat"),
            pytest.param("b:.3f \n (p:.4f)", id="with_pvalue"),
            pytest.param("b:.3f \n (se:.3f) \n [t:.2f]", id="all_stats"),
            pytest.param("b:.4f \n (se:.2f)", id="different_decimals"),
        ],
    )
    def test_coef_fmt(self, fitted_model, snapshot, coef_fmt, output_type):
        """Coefficient format variations."""
        kwargs = {} if coef_fmt is None else {"coef_fmt": coef_fmt}
        table = mt.ETable([fitted_model], **kwargs)
        assert render_table(table, output_type) == snapshot
