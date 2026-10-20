"""Base snapshot tests for pyfixest models."""

# ruff: noqa: SLF001 -- exercise the legacy pyfixest interface explicitly

from types import SimpleNamespace

import numpy as np
import pytest
from helpers import OUTPUT_TYPES, render_table

import maketables as mt
from maketables.extractors import PyFixestExtractor


def _typed_fit(model):
    """Expose a real fit through typed state, rejecting every legacy read.

    Released pyfixest fits are projected onto the upcoming state interface so
    CI tests both APIs without installing an unreleased dependency. When run
    against a typed pyfixest checkout the original state objects are used.
    """

    class TypedFit(type(model)):
        def __init__(self):
            self.tidy = model.tidy
            self._data = model._data
            if hasattr(model, "sample_info"):
                self.model = model.model
                self.sample_info = model.sample_info
                self.fitstat = model.fitstat
                self.variance_covariance = model.variance_covariance
            else:
                split = (
                    SimpleNamespace(
                        var=model._sample_split_var,
                        value=None
                        if model._sample_split_value == "all"
                        else model._sample_split_value,
                    )
                    if model._sample_split_var is not None
                    else None
                )
                self.model = SimpleNamespace(
                    depvar=model._depvar,
                    fixef=model._fixef or "",
                    sample_split=split,
                )
                self.sample_info = SimpleNamespace(n_obs=model._N)
                self.fitstat = SimpleNamespace(
                    r2=model._r2,
                    adj_r2=model._adj_r2,
                    r2_within=model._r2_within,
                    adj_r2_within=model._adj_r2_within,
                    rmse=model._rmse,
                    deviance=np.nan,
                )
                self.variance_covariance = SimpleNamespace(
                    G=tuple(model._G or ()),
                    spec=SimpleNamespace(
                        vcov_type=model._vcov_type,
                        clustervar=tuple(model._clustervar or ()),
                    ),
                )

        def __getattribute__(self, name):
            if name in {
                "_N",
                "_depvar",
                "_fixef",
                "_G",
                "_clustervar",
                "_vcov_type",
                "_r2",
                "_adj_r2",
                "_r2_adj",
                "_r2_within",
                "_adj_r2_within",
                "_rmse",
                "deviance",
                "_F_stat",
                "_f_stat_1st_stage",
                "_sample_split_var",
                "_sample_split_value",
            }:
                raise AssertionError(
                    f"Typed model must not read legacy attribute {name}"
                )
            return super().__getattribute__(name)

    return TypedFit()


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

    @pytest.mark.parametrize("typed", [False, True])
    def test_fit_state_table_content(self, simple_df, typed):
        """Labels, FE rows, fit statistics and split headers survive both APIs."""
        import pyfixest as pf

        data = simple_df.rename(columns={"y": "outcome"})
        fits = pf.feols("outcome ~ x | group", data=data, fsplit="group")
        models = list(fits.all_fitted_models.values())
        if typed:
            models = [_typed_fit(model) for model in models]
        table = mt.ETable(
            models,
            labels={"outcome": "Outcome", "x": "Exposure"},
            felabels={"group": "Region"},
            model_stats=["N", "r2", "adj_r2", "rmse"],
        )
        assert list(table.df.columns.get_level_values(0)) == ["Outcome"] * 3
        assert list(table.df.columns.get_level_values(1)) == ["all", "A", "B"]
        assert ("coef", "Exposure") in table.df.index
        assert ("fe", "Region") in table.df.index
        assert table.df.loc[("stats", "Observations")].tolist() == [
            "100",
            str(int((data["group"] == "A").sum())),
            str(int((data["group"] == "B").sum())),
        ]
        for label in ["R²", "Adj. R²", "RMSE"]:
            assert "-" not in table.df.loc[("stats", label)].tolist()
        extractor = PyFixestExtractor()
        for model in models:
            assert extractor.stat(model, "N") == len(model._data)
            assert extractor.stat(model, "r2") is not None
            assert extractor.depvar(model) == "outcome"

    def test_typed_clustered_fit(self, simple_df):
        import pyfixest as pf

        model = _typed_fit(pf.feols("y ~ x", data=simple_df, vcov={"CRV1": "group"}))
        extractor = PyFixestExtractor()
        assert extractor.stat(model, "n_clusters") == 2
        assert extractor.stat(model, "se_type") == "by: group"
        assert extractor.vcov_info(model) == {
            "vcov_type": "CRV",
            "clustervar": ["group"],
        }
        assert "r2_within" not in extractor.supported_stats(model)
