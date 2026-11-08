"""Snapshot tests for ETable coefficient formatting."""

import pytest
from helpers import OUTPUT_TYPES, render_table

import maketables as mt


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


def test_empty_signif_code_disables_stars(fitted_model):
    """signif_code=[] removes stars from cells and the significance note."""
    table = mt.ETable(fitted_model, signif_code=[])
    default = mt.ETable(fitted_model)

    b = fitted_model.coef()["x"]
    assert "*" in default.df.loc["coef"].loc["x"].iloc[0]
    assert table.df.loc["coef"].loc["x"].iloc[0].startswith(f"{b:.3f} \n")
    assert not any("*" in cell for cell in table.df.loc["coef"].to_numpy().ravel())
    assert "Significance levels" in default.notes
    assert "Significance levels" not in table.notes


@pytest.mark.parametrize("signif_code", [[0.05], [0.01, 0.05], (0.01, 0.05, 0.1)])
def test_signif_code_rejects_other_shapes(fitted_model, signif_code):
    with pytest.raises(ValueError, match="signif_code"):
        mt.ETable(fitted_model, signif_code=signif_code)
