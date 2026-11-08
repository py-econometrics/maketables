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


@pytest.mark.parametrize("statsmodels_first", [False, True])
def test_coef_fmt_token_missing_from_one_model(
    fitted_model, statsmodels_ols, statsmodels_first
):
    """A token from any model's coef table renders; models lacking it show '-'."""
    models = [fitted_model, statsmodels_ols]
    if statsmodels_first:
        models.reverse()
    table = mt.ETable(models, coef_fmt="b:.3f [ci90l:.3f, ci90u:.3f]")
    coefs = table.df.loc["coef"]

    sm_col = 0 if statsmodels_first else 1
    sm_tidy = mt.extractors.get_extractor(statsmodels_ols).coef_table(statsmodels_ols)
    b, lo, hi = sm_tidy.loc["x", ["b", "ci90l", "ci90u"]]
    assert coefs.loc["x"].iloc[sm_col] == f"{b:.3f} [{lo:.3f}, {hi:.3f}]"

    pf_cell = coefs.loc["x"].iloc[1 - sm_col]
    pf_b = fitted_model.coef()["x"]
    assert pf_cell == f"{pf_b:.3f} [-, -]"
