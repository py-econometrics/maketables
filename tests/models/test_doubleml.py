"""Tests for the DoubleML extractor."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

import maketables as mt
from maketables.extractors import DoubleMLExtractor, get_extractor

# The extractor is duck-typed and also works with doubleml 0.9.x, but the dataset
# generators these fixtures use moved into the submodules in 0.10.
dml = pytest.importorskip("doubleml", minversion="0.10", reason="needs doubleml")

from doubleml.did.datasets import make_did_CS2021  # noqa: E402
from doubleml.irm.datasets import (  # noqa: E402
    make_heterogeneous_data,
    make_irm_data,
    make_irm_data_discrete_treatments,
    make_ssm_data,
)
from doubleml.plm.datasets import (  # noqa: E402
    make_pliv_multiway_cluster_CKMS2021,
    make_plr_CCDDHNR2018,
)
from sklearn.linear_model import LinearRegression, LogisticRegression  # noqa: E402

NORM_Q95 = stats.norm.ppf(0.975)
NORM_Q90 = stats.norm.ppf(0.95)


def _reg():
    return LinearRegression()


def _clf():
    return LogisticRegression(max_iter=200)


@pytest.fixture
def plr_data():
    """Draw a partially linear DGP once per test."""
    np.random.seed(3141)
    return make_plr_CCDDHNR2018(n_obs=200, dim_x=5, return_type="DataFrame")


@pytest.fixture
def plr(plr_data):
    """Fit a partially linear regression with a single treatment."""
    np.random.seed(42)
    model = dml.DoubleMLPLR(
        dml.DoubleMLData(plr_data, "y", "d"), _reg(), _reg(), n_folds=2
    )
    model.fit()
    return model


@pytest.fixture
def plr_unfitted(plr_data):
    """Build a partially linear model without estimating it."""
    return dml.DoubleMLPLR(
        dml.DoubleMLData(plr_data, "y", "d"), _reg(), _reg(), n_folds=2
    )


@pytest.fixture
def plr_multi(plr_data):
    """Fit a partially linear regression with two treatments and repeated cross-fitting."""
    np.random.seed(42)
    data = plr_data.copy()
    data["d2"] = np.random.normal(size=len(data))
    model = dml.DoubleMLPLR(
        dml.DoubleMLData(data, "y", ["d", "d2"]), _reg(), _reg(), n_folds=2, n_rep=3
    )
    model.fit()
    return model


@pytest.fixture
def irm():
    """Fit an interactive regression model (ATE of a binary treatment)."""
    np.random.seed(42)
    data = make_irm_data(n_obs=300, dim_x=5, theta=0.5, return_type="DataFrame")
    model = dml.DoubleMLIRM(dml.DoubleMLData(data, "y", "d"), _reg(), _clf(), n_folds=2)
    model.fit()
    return model


@pytest.fixture
def ssm():
    """Fit a sample selection model (uses a dedicated DoubleMLData subclass)."""
    np.random.seed(42)
    data = make_ssm_data(n_obs=500, dim_x=5, return_type="DataFrame")
    model = dml.DoubleMLSSM(
        dml.data.DoubleMLSSMData(data, "y", "d", s_col="s"),
        _reg(),
        _clf(),
        _clf(),
        n_folds=2,
    )
    model.fit()
    return model


@pytest.fixture
def pliv_cluster():
    """Fit a partially linear IV model on two-way clustered data."""
    np.random.seed(42)
    data = make_pliv_multiway_cluster_CKMS2021(N=20, M=15, dim_X=3)
    model = dml.DoubleMLPLIV(data, _reg(), _reg(), _reg(), n_folds=2)
    model.fit()
    return model


@pytest.fixture
def qte():
    """Fit quantile treatment effects (not a subclass of DoubleML)."""
    np.random.seed(42)
    data = make_irm_data(n_obs=500, dim_x=5, theta=0.5, return_type="DataFrame")
    model = dml.DoubleMLQTE(
        dml.DoubleMLData(data, "y", "d"),
        _clf(),
        _clf(),
        quantiles=[0.25, 0.5],
        n_folds=2,
    )
    model.fit()
    return model


@pytest.fixture
def apos():
    """Fit average potential outcomes (not a subclass of DoubleML)."""
    np.random.seed(42)
    raw = make_irm_data_discrete_treatments(n_obs=300)
    data = pd.DataFrame(
        np.column_stack((raw["y"], raw["d"], raw["x"])),
        columns=["y", "d"] + [f"x{i}" for i in range(raw["x"].shape[1])],
    )
    model = dml.DoubleMLAPOS(
        dml.DoubleMLData(data, "y", "d"),
        _reg(),
        _clf(),
        treatment_levels=[0, 1, 2],
        n_folds=2,
    )
    model.fit()
    return model


@pytest.fixture
def gate():
    """Fit group average treatment effects (a DoubleMLBLP, not a DoubleML)."""
    np.random.seed(42)
    data = make_heterogeneous_data(
        n_obs=400, p=5, support_size=5, n_x=1, binary_treatment=True
    )["data"]
    model = dml.DoubleMLIRM(dml.DoubleMLData(data, "y", "d"), _reg(), _clf(), n_folds=2)
    model.fit()
    groups = pd.DataFrame(
        {"Group": pd.qcut(data["X_0"], 3, labels=["low", "mid", "high"])}
    )
    return model.gate(groups)


@pytest.fixture
def did_multi():
    """Fit multi-period difference-in-differences (not a subclass of DoubleML)."""
    np.random.seed(42)
    panel = make_did_CS2021(n_obs=300, dgp_type=1)
    data = dml.data.DoubleMLPanelData(
        panel,
        y_col="y",
        d_cols="d",
        id_col="id",
        t_col="t",
        x_cols=["Z1", "Z2", "Z3", "Z4"],
    )
    model = dml.did.DoubleMLDIDMulti(
        data, _reg(), _clf(), gt_combinations="standard", n_folds=2
    )
    model.fit()
    return model


class TestDispatch:
    """The registry must route doubleml objects to the DoubleML extractor."""

    @pytest.mark.parametrize(
        "name",
        [
            "plr",
            "plr_multi",
            "irm",
            "ssm",
            "pliv_cluster",
            "qte",
            "apos",
            "did_multi",
            "gate",
        ],
    )
    def test_extractor_is_selected(self, name, request):
        """Every doubleml result type is routed to the DoubleML extractor."""
        model = request.getfixturevalue(name)
        assert isinstance(get_extractor(model), DoubleMLExtractor)

    def test_unfitted_model_is_claimed(self, plr_unfitted):
        """An unfitted model is still claimed, so the user gets a useful error."""
        assert isinstance(get_extractor(plr_unfitted), DoubleMLExtractor)

    def test_non_doubleml_models_are_untouched(self, statsmodels_ols):
        """Models from other packages are left to their own extractors."""
        assert not DoubleMLExtractor().can_handle(statsmodels_ols)

    def test_doubleml_data_is_not_a_model(self, plr_data):
        """A DoubleMLData container is not a result object."""
        data = dml.DoubleMLData(plr_data, "y", "d")
        assert not DoubleMLExtractor().can_handle(data)


class TestCoefTable:
    """The coefficient table must reproduce doubleml's own inference."""

    def test_columns_match_summary(self, plr):
        """The canonical tokens carry doubleml's own summary values."""
        table = DoubleMLExtractor().coef_table(plr)
        summary = plr.summary
        assert table.index.name == "Coefficient"
        assert list(table.index) == [str(i) for i in summary.index]
        np.testing.assert_allclose(table["b"], summary["coef"])
        np.testing.assert_allclose(table["se"], summary["std err"])
        np.testing.assert_allclose(table["t"], summary["t"])
        np.testing.assert_allclose(table["p"], summary["P>|t|"])

    def test_t_and_z_are_the_same_statistic(self, plr):
        """DoubleML uses a normal approximation, so `t` and `z` are aliases."""
        table = DoubleMLExtractor().coef_table(plr)
        np.testing.assert_allclose(table["t"], table["z"])

    def test_statistic_equals_coef_over_se(self, plr_multi):
        """The reported statistic is the coefficient over its standard error."""
        table = DoubleMLExtractor().coef_table(plr_multi)
        np.testing.assert_allclose(table["t"], table["b"] / table["se"], rtol=1e-10)

    def test_pvalues_are_two_sided_normal(self, plr_multi):
        """Recompute p from (b, se) independently of doubleml's summary."""
        table = DoubleMLExtractor().coef_table(plr_multi)
        expected = 2 * stats.norm.sf(np.abs(table["b"] / table["se"]))
        np.testing.assert_allclose(table["p"], expected, rtol=1e-8, atol=1e-12)

    def test_confidence_intervals_match_confint(self, plr_multi):
        """Both interval levels come from confint()."""
        table = DoubleMLExtractor().coef_table(plr_multi)
        ci95 = plr_multi.confint(level=0.95)
        ci90 = plr_multi.confint(level=0.90)
        np.testing.assert_allclose(table["ci95l"], ci95.iloc[:, 0])
        np.testing.assert_allclose(table["ci95u"], ci95.iloc[:, 1])
        np.testing.assert_allclose(table["ci90l"], ci90.iloc[:, 0])
        np.testing.assert_allclose(table["ci90u"], ci90.iloc[:, 1])

    def test_confidence_intervals_are_normal_based(self, plr):
        """Second, independent route to the same interval."""
        table = DoubleMLExtractor().coef_table(plr)
        np.testing.assert_allclose(
            table["ci95l"], table["b"] - NORM_Q95 * table["se"], rtol=1e-8
        )
        np.testing.assert_allclose(
            table["ci90u"], table["b"] + NORM_Q90 * table["se"], rtol=1e-8
        )

    def test_multiple_treatments_give_multiple_rows(self, plr_multi):
        """One row per treatment variable."""
        table = DoubleMLExtractor().coef_table(plr_multi)
        assert list(table.index) == ["d", "d2"]

    def test_quantiles_are_labelled(self, qte):
        """QTE rows are named by their quantile, not by a bare number."""
        table = DoubleMLExtractor().coef_table(qte)
        assert list(table.index) == ["Q(0.25)", "Q(0.5)"]
        np.testing.assert_allclose(table["b"], qte.coef)

    def test_treatment_levels_are_labelled(self, apos):
        """APOS rows are named by treatment variable and level."""
        table = DoubleMLExtractor().coef_table(apos)
        assert list(table.index) == ["d=0", "d=1", "d=2"]
        np.testing.assert_allclose(table["b"], apos.coef)

    def test_did_group_time_labels_are_preserved(self, did_multi):
        """DIDMulti rows keep doubleml's group-time labels."""
        table = DoubleMLExtractor().coef_table(did_multi)
        assert list(table.index) == list(did_multi.gt_labels)
        np.testing.assert_allclose(table["b"], did_multi.coef)

    def test_group_effects_use_the_group_names(self, gate):
        """GATE/CATE objects report a `[lower, effect, upper]` confint layout."""
        table = DoubleMLExtractor().coef_table(gate)
        assert list(table.index) == ["Group_low", "Group_mid", "Group_high"]
        np.testing.assert_allclose(table["b"], gate.summary["coef"])
        ci = gate.confint()
        np.testing.assert_allclose(table["ci95l"], ci["2.5 %"])
        np.testing.assert_allclose(table["ci95u"], ci["97.5 %"])
        # the middle "effect" column must not be mistaken for a bound
        assert not np.allclose(table["ci95u"], ci["effect"])

    def test_unfitted_model_raises_a_useful_error(self, plr_unfitted):
        """An unfitted model points the user at fit()."""
        with pytest.raises(ValueError, match=r"fit\(\)"):
            DoubleMLExtractor().coef_table(plr_unfitted)

    def test_etable_on_unfitted_model_raises(self, plr_unfitted):
        """The same error surfaces through ETable."""
        with pytest.raises(ValueError, match=r"fit\(\)"):
            mt.ETable([plr_unfitted])


class TestMetadata:
    """Dependent variable, stats and vcov information."""

    def test_depvar(self, plr, irm, did_multi):
        """The outcome name comes from the attached DoubleMLData."""
        extractor = DoubleMLExtractor()
        assert extractor.depvar(plr) == "y"
        assert extractor.depvar(irm) == "y"
        assert extractor.depvar(did_multi) == "y"

    def test_no_fixed_effects(self, plr):
        """DoubleML models carry no fixed effects specification."""
        assert DoubleMLExtractor().fixef_string(plr) is None

    def test_sample_size(self, plr, qte, apos, did_multi):
        """N is found for estimators that do and do not expose n_obs."""
        extractor = DoubleMLExtractor()
        assert extractor.stat(plr, "N") == 200
        assert extractor.stat(qte, "N") == 500
        assert extractor.stat(apos, "N") == 300
        assert isinstance(extractor.stat(did_multi, "N"), int)

    def test_resampling_stats(self, plr_multi):
        """Folds and repetitions are reported as set."""
        extractor = DoubleMLExtractor()
        assert extractor.stat(plr_multi, "n_folds") == 2
        assert extractor.stat(plr_multi, "n_rep") == 3

    def test_score_and_learners(self, plr, irm):
        """Score function and nuisance learner classes are reported."""
        extractor = DoubleMLExtractor()
        assert extractor.stat(plr, "score") == "partialling out"
        assert extractor.stat(irm, "score") == "ATE"
        assert extractor.stat(plr, "learners") == "LinearRegression"
        assert extractor.stat(irm, "learners") == "LinearRegression, LogisticRegression"

    def test_unknown_stat_returns_none(self, plr):
        """Statistics that do not apply return None rather than raising."""
        assert DoubleMLExtractor().stat(plr, "r2") is None

    def test_clustering(self, pliv_cluster, plr):
        """Cluster-robust inference is reflected in vcov info and stats."""
        extractor = DoubleMLExtractor()
        info = extractor.vcov_info(pliv_cluster)
        assert info["vcov_type"] == "cluster"
        assert info["clustervar"] == ["cluster_var_i", "cluster_var_j"]
        assert extractor.stat(pliv_cluster, "se_type").startswith("by: ")
        assert (
            extractor.stat(pliv_cluster, "n_clusters") == 20
        )  # first dimension of 20 x 15

        assert extractor.vcov_info(plr) == {
            "vcov_type": "asymptotic",
            "clustervar": None,
        }
        assert extractor.stat(plr, "se_type") == "asymptotic"
        assert extractor.stat(plr, "n_clusters") is None

    def test_group_effect_stats_omit_what_is_missing(self, gate):
        """A BLP has no data object, folds or score -- those rows must not appear."""
        extractor = DoubleMLExtractor()
        assert extractor.default_stat_keys(gate) == ["N"]
        assert extractor.stat(gate, "N") == 400
        assert extractor.stat(gate, "score") is None
        assert extractor.stat(gate, "n_folds") is None

    def test_supported_stats(self, plr):
        """Only statistics the model can actually provide are advertised."""
        supported = DoubleMLExtractor().supported_stats(plr)
        assert {"N", "n_folds", "n_rep", "score", "learners"} <= supported
        assert "n_clusters" not in supported

    def test_default_stats_are_labelled(self, plr):
        """Every default statistic has a printable label."""
        extractor = DoubleMLExtractor()
        labels = extractor.stat_labels(plr)
        for key in extractor.default_stat_keys(plr):
            assert key in labels or key in mt.ETable.DEFAULT_STAT_LABELS

    def test_default_stats_only_mention_what_is_used(
        self, plr, plr_multi, pliv_cluster
    ):
        """Clustering and repetition rows appear only when they apply."""
        extractor = DoubleMLExtractor()
        assert extractor.default_stat_keys(plr) == ["N", "score", "n_folds"]
        # repeated cross-fitting and clustering earn a row only when present
        assert "n_rep" in extractor.default_stat_keys(plr_multi)
        assert "n_clusters" in extractor.default_stat_keys(pliv_cluster)

    def test_var_labels_are_read_from_the_source_data(self, plr_data):
        """Variable labels set on the source DataFrame reach the table."""
        from maketables.importdta import set_var_labels

        data = plr_data.copy()
        set_var_labels(data, {"d": "Treatment"})
        np.random.seed(42)
        model = dml.DoubleMLPLR(
            dml.DoubleMLData(data, "y", "d"), _reg(), _reg(), n_folds=2
        )
        model.fit()
        assert DoubleMLExtractor().var_labels(model)["d"] == "Treatment"


class TestETable:
    """End-to-end rendering."""

    def test_latex_shows_the_point_estimate(self, plr):
        """LaTeX output carries the estimate and standard error."""
        tex = mt.ETable([plr]).make(type="tex")
        assert f"{plr.coef[0]:.3f}" in tex
        assert f"{plr.se[0]:.3f}" in tex

    def test_html_renders(self, plr):
        """Great Tables HTML output carries the estimate."""
        html = mt.ETable([plr]).make(type="gt").as_raw_html()
        assert f"{plr.coef[0]:.3f}" in html

    def test_typst_renders(self, plr):
        """Typst output carries the estimate."""
        assert f"{plr.coef[0]:.3f}" in mt.ETable([plr]).make(type="typst")

    def test_default_stats_appear(self, plr):
        """The default bottom panel reports the sample size."""
        tex = mt.ETable([plr]).make(type="tex")
        assert "Observations" in tex
        assert "200" in tex

    def test_several_doubleml_models_in_one_table(self, plr, irm):
        """Two doubleml models share one table."""
        tex = mt.ETable([plr, irm]).make(type="tex")
        assert f"{plr.coef[0]:.3f}" in tex
        assert f"{irm.coef[0]:.3f}" in tex

    def test_mixed_with_statsmodels(self, plr, statsmodels_ols):
        """DoubleML models must compose with the other supported packages."""
        tex = mt.ETable([statsmodels_ols, plr]).make(type="tex")
        assert f"{plr.coef[0]:.3f}" in tex

    def test_coef_fmt_tokens(self, plr):
        """Confidence bounds are addressable from coef_fmt."""
        tex = mt.ETable([plr], coef_fmt="b [ci95l, ci95u]").make(type="tex")
        assert f"{plr.confint().iloc[0, 0]:.3f}" in tex

    def test_labels_can_rename_rows(self, plr):
        """Treatment rows can be relabelled like any other coefficient."""
        tex = mt.ETable([plr], labels={"d": "Treatment"}).make(type="tex")
        assert "Treatment" in tex

    def test_inspect_model_reports_columns_and_stats(self, plr, capsys):
        """inspect_model discovers the doubleml tokens and statistics."""
        mt.inspect_model(plr)
        out = capsys.readouterr().out
        assert "DoubleMLExtractor" in out
        assert "ci95l" in out
        assert "n_folds" in out
