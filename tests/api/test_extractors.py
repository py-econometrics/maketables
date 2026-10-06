# ruff: noqa: SLF001, D101, FBT002
import re
import types

import numpy as np
import pandas as pd
import pytest

from maketables import extractors as ex
from maketables.extractors import (
    LinearmodelsExtractor,
    PluginExtractor,
    PyFixestExtractor,
    StatsmodelsExtractor,
    get_extractor,
    inspect_model,
    register_extractor,
)

# ---------------------------------------------------------------- registry


@pytest.fixture
def clean_registry(monkeypatch):
    """Run with an isolated registry; the global one is restored afterwards."""
    monkeypatch.setattr(ex, "_EXTRACTOR_REGISTRY", [])
    return ex._EXTRACTOR_REGISTRY


class _Dummy:
    pass


class _DummyExtractor:
    def __init__(self, handles=True, raises=False):
        self.handles = handles
        self.raises = raises

    def can_handle(self, model):
        if self.raises:
            raise RuntimeError("boom")
        return self.handles


def test_builtin_extractors_registered_in_order():
    names = [type(e).__name__ for e in ex._EXTRACTOR_REGISTRY]
    assert names[:3] == [
        "PyFixestExtractor",
        "LinearmodelsExtractor",
        "StatsmodelsExtractor",
    ]


def test_register_extractor_appends_and_is_used(clean_registry):
    mine = _DummyExtractor()
    register_extractor(mine)
    assert clean_registry == [mine]
    assert get_extractor(_Dummy()) is mine


def test_get_extractor_first_match_wins_and_skips_failing(clean_registry):
    bad = _DummyExtractor(raises=True)
    no = _DummyExtractor(handles=False)
    first = _DummyExtractor()
    second = _DummyExtractor()
    for e in (bad, no, first, second):
        register_extractor(e)
    assert get_extractor(_Dummy()) is first


def test_clear_extractors(clean_registry):
    register_extractor(_DummyExtractor())
    ex.clear_extractors()
    assert clean_registry == []


def test_get_extractor_unknown_model_error_message(clean_registry):
    register_extractor(_DummyExtractor(handles=False))
    with pytest.raises(TypeError) as exc:
        get_extractor(_Dummy())
    msg = str(exc.value)
    assert "_Dummy" in msg
    assert "Registered extractors (1)" in msg
    assert "_DummyExtractor" in msg
    assert "__maketables_coef_table__" in msg


def test_get_extractor_falls_back_to_plugin(clean_registry):
    class Plug:
        __maketables_coef_table__ = pd.DataFrame({"b": [1.0]}, index=["x"])

    assert isinstance(get_extractor(Plug()), PluginExtractor)


def test_get_extractor_plugin_check_exception_is_swallowed(clean_registry):
    class Weird:
        @property
        def __maketables_coef_table__(self):
            raise RuntimeError("no")

    # hasattr only swallows AttributeError, so can_handle raises -> TypeError
    with pytest.raises(TypeError):
        get_extractor(Weird())


def test_builtin_dispatch(
    fitted_model, statsmodels_ols, linearmodels_panelols, linearmodels_iv2sls
):
    assert isinstance(get_extractor(fitted_model), PyFixestExtractor)
    assert isinstance(get_extractor(statsmodels_ols), StatsmodelsExtractor)
    assert isinstance(get_extractor(linearmodels_panelols), LinearmodelsExtractor)
    assert isinstance(get_extractor(linearmodels_iv2sls), LinearmodelsExtractor)


def test_protocol_is_runtime_checkable():
    for cls in (
        PyFixestExtractor,
        StatsmodelsExtractor,
        LinearmodelsExtractor,
        PluginExtractor,
    ):
        assert isinstance(cls(), ex.ModelExtractor)


def test_from_package_checks_mro():
    class Base:
        pass

    Base.__module__ = "fakepkg.sub"

    class Child(Base):
        pass

    Child.__module__ = "elsewhere"
    assert ex._from_package(Child(), "fakepkg")
    assert not ex._from_package(Child(), "other")


# ---------------------------------------------------------------- helpers


def test_helpers():
    assert ex._first_if_sequence([3, 4]) == 3
    assert ex._first_if_sequence(np.array([5, 6])) == 5
    assert ex._first_if_sequence(7) == 7
    assert ex._sum_if_not_none(None) is None
    assert ex._sum_if_not_none(pd.Series([1, 2])) == 3
    w = pd.Series([1, 2, 3])
    e = pd.Series([1, 0, 1])
    assert ex._sum_observed_events(w, e) == 4
    assert ex._sum_observed_events(None, e) is None
    assert ex._sum_observed_events(w, None) is None


def test_follow_and_get_attr():
    obj = types.SimpleNamespace(a=types.SimpleNamespace(b=types.SimpleNamespace(c=5)))
    assert ex._follow(obj, ["a", "b", "c"]) == 5
    assert ex._follow(obj, ["a", "x", "c"]) is None

    wrapped = types.SimpleNamespace(model=types.SimpleNamespace(nobs=10), v=1)
    assert ex._get_attr(wrapped, "v") == 1
    assert ex._get_attr(wrapped, "nobs") == 10  # falls back to model.nobs
    assert ex._get_attr(wrapped, "missing") is None
    assert ex._get_attr(wrapped, ("model", "nobs")) == 10
    assert ex._get_attr(wrapped, lambda m: m.v + 1) == 2
    assert ex._get_attr(wrapped, lambda m: m.nope) is None  # error -> None
    assert ex._get_attr(wrapped, 3.14) is None  # unsupported spec


def test_pyfixest_types_present():
    assert len(ex._pyfixest_types()) == 3
    assert len(ex._linearmodels_types()) == 2


def test_missing_packages_return_empty(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake(name, *a, **k):
        if name.startswith(("pyfixest", "linearmodels")):
            raise ImportError(name)
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    assert ex._pyfixest_types() == ()
    assert ex._linearmodels_types() == ()


# ---------------------------------------------------------------- plugin


class _PluginModel:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def _plugin(**attrs):
    # dunder-style names cannot be passed via ** easily; set on a class
    cls = type("PM", (), {f"__maketables_{k}__": v for k, v in attrs.items()})
    return cls()


class TestPluginExtractor:
    def test_coef_table_sets_index_name_without_mutating(self):
        df = pd.DataFrame({"b": [1.0], "se": [0.1], "p": [0.5]}, index=["x"])
        m = _plugin(coef_table=df)
        out = PluginExtractor().coef_table(m)
        assert out.index.name == "Coefficient"
        assert df.index.name is None

    def test_coef_table_keeps_existing_index_name(self):
        df = pd.DataFrame({"b": [1.0]}, index=pd.Index(["x"], name="Coefficient"))
        out = PluginExtractor().coef_table(_plugin(coef_table=df))
        assert out is df

    def test_coef_table_rejects_non_dataframe(self):
        with pytest.raises(ValueError, match=r"must return a pd\.DataFrame"):
            PluginExtractor().coef_table(_plugin(coef_table={"b": 1}))

    def test_defaults_when_attributes_missing(self):
        p = PluginExtractor()
        m = _plugin(coef_table=pd.DataFrame({"b": [1.0]}))
        assert p.depvar(m) == "Dependent Variable"
        assert p.fixef_string(m) is None
        assert p.stat(m, "N") is None
        assert p.vcov_info(m) == {}
        assert p.var_labels(m) is None
        assert p.stat_labels(m) is None
        assert p.default_stat_keys(m) is None
        assert p.supported_stats(m) == set()
        assert p.sample_split(m) is None

    def test_attributes_are_used(self):
        p = PluginExtractor()
        m = _plugin(
            coef_table=pd.DataFrame({"b": [1.0]}),
            depvar="wage",
            fixef_string="firm",
            var_labels={"x": "X"},
            vcov_info={"vcov_type": "HC1"},
            stat_labels={"N": "Obs"},
            default_stat_keys=["N", "r2"],
            stat=lambda _self, key: {"N": 5}.get(key),
        )
        assert p.depvar(m) == "wage"
        assert p.fixef_string(m) == "firm"
        assert p.var_labels(m) == {"x": "X"}
        assert p.vcov_info(m) == {"vcov_type": "HC1"}
        assert p.stat_labels(m) == {"N": "Obs"}
        assert p.default_stat_keys(m) == ["N", "r2"]
        assert p.stat(m, "N") == 5
        assert p.stat(m, "zzz") is None
        assert p.supported_stats(m) == set()

    def test_invalid_vcov_and_default_keys_ignored(self):
        p = PluginExtractor()
        m = _plugin(vcov_info="oops", default_stat_keys=["N", 3])
        assert p.vcov_info(m) == {}
        assert p.default_stat_keys(m) is None
        m2 = _plugin(default_stat_keys="N")
        assert p.default_stat_keys(m2) is None


# ---------------------------------------------------------------- statsmodels


class TestStatsmodelsExtractor:
    def test_coef_table(self, statsmodels_ols):
        df = StatsmodelsExtractor().coef_table(statsmodels_ols)
        assert list(df.columns) == [
            "b",
            "se",
            "t",
            "p",
            "ci95l",
            "ci95u",
            "ci90l",
            "ci90u",
        ]
        assert df.index.name == "Coefficient"
        assert list(df.index) == ["Intercept", "x"]
        np.testing.assert_allclose(df["b"], statsmodels_ols.params)
        np.testing.assert_allclose(df["se"], statsmodels_ols.bse)
        np.testing.assert_allclose(df["p"], statsmodels_ols.pvalues)
        ci = statsmodels_ols.conf_int(alpha=0.10)
        np.testing.assert_allclose(df["ci90l"], ci.iloc[:, 0])
        # 95% interval is wider than the 90% one
        assert (df["ci95l"] < df["ci90l"]).all()
        assert (df["ci95u"] > df["ci90u"]).all()

    def test_coef_table_fallback_without_conf_int(self):
        m = types.SimpleNamespace(
            params=pd.Series([1.0, 2.0], index=["a", "b"]),
            bse=pd.Series([0.5, 0.5], index=["a", "b"]),
            pvalues=pd.Series([0.1, 0.01], index=["a", "b"]),
        )
        df = StatsmodelsExtractor().coef_table(m)
        assert "t" not in df.columns
        np.testing.assert_allclose(df["ci95l"], [1 - 0.98, 2 - 0.98])
        np.testing.assert_allclose(df["ci90u"], [1 + 0.8225, 2 + 0.8225])

    def test_coef_table_fallback_when_conf_int_fails(self):
        def bad(alpha=0.05):
            raise RuntimeError

        m = types.SimpleNamespace(
            params=pd.Series([1.0], index=["a"]),
            bse=pd.Series([1.0], index=["a"]),
            pvalues=pd.Series([0.1], index=["a"]),
            tvalues=pd.Series([1.0], index=["a"]),
            conf_int=bad,
        )
        df = StatsmodelsExtractor().coef_table(m)
        assert df["ci95l"].iloc[0] == pytest.approx(-0.96)
        assert df["ci90u"].iloc[0] == pytest.approx(2.645)
        assert df["t"].iloc[0] == 1.0

    def test_stats(self, statsmodels_ols, statsmodels_logit):
        e = StatsmodelsExtractor()
        assert e.stat(statsmodels_ols, "N") == 100
        assert isinstance(e.stat(statsmodels_ols, "N"), int)
        assert e.stat(statsmodels_ols, "r2") == pytest.approx(statsmodels_ols.rsquared)
        assert e.stat(statsmodels_ols, "se_type") == "nonrobust"
        assert e.stat(statsmodels_ols, "not_a_stat") is None
        assert e.stat(statsmodels_logit, "pseudo_r2") == pytest.approx(
            statsmodels_logit.prsquared
        )
        assert e.stat(statsmodels_logit, "r2") is None

    def test_n_fallback_when_not_integer(self):
        m = types.SimpleNamespace(nobs="many")
        assert StatsmodelsExtractor().stat(m, "N") == "many"

    def test_supported_stats(self, statsmodels_ols, statsmodels_logit):
        e = StatsmodelsExtractor()
        ols = e.supported_stats(statsmodels_ols)
        assert {"N", "r2", "adj_r2", "aic", "bic", "fvalue"} <= ols
        logit = e.supported_stats(statsmodels_logit)
        assert "pseudo_r2" in logit
        assert "r2" not in logit

    def test_depvar(self, statsmodels_ols, statsmodels_logit):
        e = StatsmodelsExtractor()
        assert e.depvar(statsmodels_ols) == "y"
        assert e.depvar(statsmodels_logit) == "y_binary"
        assert e.depvar(types.SimpleNamespace()) == "y"
        assert e.depvar(types.SimpleNamespace(endog_names="z")) == "z"
        nested = types.SimpleNamespace(
            model=types.SimpleNamespace(endog=types.SimpleNamespace(name="w"))
        )
        assert e.depvar(nested) == "w"

    def test_vcov_fixef_split(self, statsmodels_ols):
        e = StatsmodelsExtractor()
        assert e.vcov_info(statsmodels_ols) == {
            "vcov_type": "nonrobust",
            "clustervar": None,
        }
        assert e.fixef_string(statsmodels_ols) is None
        assert e.sample_split(statsmodels_ols) is None
        assert e.stat_labels(statsmodels_ols) is None

    def test_default_stat_keys(
        self, statsmodels_ols, statsmodels_logit, statsmodels_probit
    ):
        e = StatsmodelsExtractor()
        assert e.default_stat_keys(statsmodels_ols) is None
        assert e.default_stat_keys(statsmodels_logit) == ["N", "pseudo_r2", "ll"]
        assert e.default_stat_keys(statsmodels_probit) == ["N", "pseudo_r2", "ll"]
        assert e.default_stat_keys(types.SimpleNamespace()) is None

    def test_var_labels(self, statsmodels_ols):
        e = StatsmodelsExtractor()
        labels = e.var_labels(statsmodels_ols)
        assert isinstance(labels, dict)
        assert e.var_labels(types.SimpleNamespace()) is None

    def test_var_labels_failure_returns_none(self, monkeypatch, statsmodels_ols):
        def boom(*a, **k):
            raise RuntimeError

        monkeypatch.setattr(ex, "get_var_labels", boom)
        assert StatsmodelsExtractor().var_labels(statsmodels_ols) is None

    def test_can_handle(self, statsmodels_ols):
        e = StatsmodelsExtractor()
        assert e.can_handle(statsmodels_ols)
        assert not e.can_handle(_Dummy())


# ---------------------------------------------------------------- linearmodels


class TestLinearmodelsExtractor:
    def test_can_handle(self, linearmodels_panelols, statsmodels_ols):
        e = LinearmodelsExtractor()
        assert e.can_handle(linearmodels_panelols)
        assert not e.can_handle(statsmodels_ols)
        assert not e.can_handle(_Dummy())

    def test_can_handle_attribute_fallback(self, monkeypatch):
        class Res:
            params = 1
            pvalues = 1
            std_errors = 1

        Res.__module__ = "linearmodels.custom"
        e = LinearmodelsExtractor()
        assert e.can_handle(Res())

        class NoSE:
            params = 1
            pvalues = 1

        NoSE.__module__ = "linearmodels.custom"
        assert not e.can_handle(NoSE())

        monkeypatch.setattr(ex, "_linearmodels_types", lambda: ())
        assert not e.can_handle(Res())

    @pytest.mark.parametrize(
        "fixture", ["linearmodels_panelols", "linearmodels_absorbingls"]
    )
    def test_coef_table(self, request, fixture):
        model = request.getfixturevalue(fixture)
        df = LinearmodelsExtractor().coef_table(model)
        assert list(df.columns) == [
            "b",
            "se",
            "t",
            "p",
            "ci95l",
            "ci95u",
            "ci90l",
            "ci90u",
        ]
        np.testing.assert_allclose(df["b"], model.params)
        np.testing.assert_allclose(df["p"], model.pvalues)
        assert (df["ci95l"] < df["ci90l"]).all()

    def test_coef_table_iv_uses_std_error(self, linearmodels_iv2sls):
        df = LinearmodelsExtractor().coef_table(linearmodels_iv2sls)
        np.testing.assert_allclose(df["se"], linearmodels_iv2sls.std_errors)
        assert "x_endog" in df.index

    def test_coef_table_fallbacks(self):
        idx = ["a"]
        base = {
            "params": pd.Series([1.0], index=idx),
            "std_error": pd.Series([1.0], index=idx),
            "pvalues": pd.Series([0.2], index=idx),
        }
        e = LinearmodelsExtractor()
        df = e.coef_table(types.SimpleNamespace(**base))
        assert "t" not in df.columns
        assert df["ci95u"].iloc[0] == pytest.approx(2.96)
        assert df["ci90l"].iloc[0] == pytest.approx(1 - 1.645)

        def bad(level=0.95):
            raise RuntimeError

        df = e.coef_table(types.SimpleNamespace(conf_int=bad, **base))
        assert df["ci95l"].iloc[0] == pytest.approx(-0.96)
        assert df["ci90u"].iloc[0] == pytest.approx(2.645)

    def test_stats_panel(self, linearmodels_panelols):
        e = LinearmodelsExtractor()
        assert e.stat(linearmodels_panelols, "N") == 100
        assert isinstance(e.stat(linearmodels_panelols, "N"), int)
        assert e.stat(linearmodels_panelols, "r2") == pytest.approx(
            linearmodels_panelols.rsquared
        )
        assert e.stat(linearmodels_panelols, "r2_within") == pytest.approx(
            linearmodels_panelols.rsquared_within
        )
        assert e.stat(linearmodels_panelols, "fvalue") == pytest.approx(
            linearmodels_panelols.f_statistic.stat
        )
        assert e.stat(linearmodels_panelols, "f_pvalue") == pytest.approx(
            linearmodels_panelols.f_statistic.pval
        )
        assert e.stat(linearmodels_panelols, "nope") is None
        sup = e.supported_stats(linearmodels_panelols)
        assert {"N", "r2", "r2_within", "fvalue"} <= sup

    def test_rmse_branches(self):
        e = LinearmodelsExtractor()
        assert e.stat(types.SimpleNamespace(root_mean_squared_error=2.0), "rmse") == 2.0
        assert e.stat(types.SimpleNamespace(s2=4.0), "rmse") == 2.0
        assert e.stat(types.SimpleNamespace(s2=None), "rmse") is None
        assert e.stat(types.SimpleNamespace(), "rmse") is None

    def test_n_fallback_when_not_integer(self):
        assert LinearmodelsExtractor().stat(types.SimpleNamespace(nobs="x"), "N") == "x"

    def test_depvar(
        self,
        linearmodels_panelols,
        linearmodels_pooledols,
        linearmodels_absorbingls,
        linearmodels_iv2sls,
    ):
        e = LinearmodelsExtractor()
        assert e.depvar(linearmodels_panelols) == "y"
        assert e.depvar(linearmodels_pooledols) == "y"
        assert e.depvar(linearmodels_absorbingls) == "y"
        assert e.depvar(linearmodels_iv2sls) == "y"

    def test_depvar_fallbacks(self):
        e = LinearmodelsExtractor()
        assert e.depvar(types.SimpleNamespace()) == "y"
        # formula without '~' is returned as is
        formula = types.SimpleNamespace(model=types.SimpleNamespace(formula="out"))
        assert e.depvar(formula) == "out"
        # dependent with .cols / .dataframe
        cols = types.SimpleNamespace(
            model=types.SimpleNamespace(dependent=types.SimpleNamespace(cols=["wage"]))
        )
        assert e.depvar(cols) == "wage"
        df = types.SimpleNamespace(
            model=types.SimpleNamespace(
                dependent=types.SimpleNamespace(dataframe=pd.DataFrame({"hours": [1]}))
            )
        )
        assert e.depvar(df) == "hours"
        empty = types.SimpleNamespace(
            model=types.SimpleNamespace(dependent=types.SimpleNamespace(cols=[]))
        )
        assert e.depvar(empty) == "y"

    def test_fixef_string(
        self, linearmodels_panelols, linearmodels_pooledols, linearmodels_absorbingls
    ):
        e = LinearmodelsExtractor()
        assert e.fixef_string(linearmodels_panelols) == "entity"
        assert e.fixef_string(linearmodels_pooledols) is None
        assert e.fixef_string(linearmodels_absorbingls) == "firm_id"
        assert e.fixef_string(types.SimpleNamespace()) is None

    def test_fixef_string_entity_time_other(self, panel_df):
        from linearmodels import PanelOLS

        e = LinearmodelsExtractor()
        res = PanelOLS.from_formula(
            "y ~ x1 + EntityEffects + TimeEffects", data=panel_df
        ).fit()
        assert e.fixef_string(res) == "entity+time"

        mdl = types.SimpleNamespace(
            entity_effects=False,
            time_effects=False,
            other_effects=object(),
            dependent=None,
        )
        assert e.fixef_string(types.SimpleNamespace(model=mdl)) == "other"

    def test_fixef_string_absorbingls_variants(self):
        class AbsorbingLS:
            def __init__(self, absorb):
                self._absorb = absorb

        e = LinearmodelsExtractor()
        no_absorb = types.SimpleNamespace(model=AbsorbingLS(None))
        assert e.fixef_string(no_absorb) is None
        wrapped = types.SimpleNamespace(
            pandas=pd.DataFrame({"a": [1], "b": [2]}),
        )
        assert (
            e.fixef_string(types.SimpleNamespace(model=AbsorbingLS(wrapped))) == "a+b"
        )
        unknown = types.SimpleNamespace(model=AbsorbingLS(object()))
        assert e.fixef_string(unknown) is None

    def test_se_type_for_iv(self, linearmodels_iv2sls):
        e = LinearmodelsExtractor()
        assert e.vcov_info(linearmodels_iv2sls)["vcov_type"] == "robust"

    def test_misc_methods(self, linearmodels_panelols):
        e = LinearmodelsExtractor()
        info = e.vcov_info(linearmodels_panelols)
        # PanelEffectsResults only exposes a private _cov_type, so the extractor
        # reports None for panel models (IV results do expose cov_type).
        assert info == {"vcov_type": None, "clustervar": None}
        assert e.stat(linearmodels_panelols, "se_type") is None
        assert e.stat_labels(linearmodels_panelols) is None
        assert e.default_stat_keys(linearmodels_panelols) is None
        assert e.sample_split(linearmodels_panelols) is None

    def test_var_labels(self):
        e = LinearmodelsExtractor()
        assert e.var_labels(types.SimpleNamespace()) is None
        df = pd.DataFrame({"x": [1]})
        m = types.SimpleNamespace(model=types.SimpleNamespace(dataframe=df))
        assert isinstance(e.var_labels(m), dict)

    def test_var_labels_failure_returns_none(self, monkeypatch):
        def boom(*a, **k):
            raise RuntimeError

        monkeypatch.setattr(ex, "get_var_labels", boom)
        m = types.SimpleNamespace(
            model=types.SimpleNamespace(dataframe=pd.DataFrame({"x": [1]}))
        )
        assert LinearmodelsExtractor().var_labels(m) is None


# ---------------------------------------------------------------- pyfixest


class TestPyFixestExtractor:
    def test_can_handle(self, fitted_model, statsmodels_ols):
        e = PyFixestExtractor()
        assert e.can_handle(fitted_model)
        assert not e.can_handle(statsmodels_ols)
        assert not e.can_handle(_Dummy())

    def test_can_handle_without_pyfixest_types(self, monkeypatch, fitted_model):
        monkeypatch.setattr(ex, "_pyfixest_types", lambda: ())
        assert not PyFixestExtractor().can_handle(fitted_model)

    def test_coef_table(self, fitted_model):
        df = PyFixestExtractor().coef_table(fitted_model)
        assert list(df.columns[:4]) == ["b", "se", "t", "p"]
        assert {"ci95l", "ci95u"} <= set(df.columns)
        tidy = fitted_model.tidy()
        np.testing.assert_allclose(df["b"], tidy["Estimate"])
        np.testing.assert_allclose(df["p"], tidy["Pr(>|t|)"])

    def test_coef_table_missing_columns(self):
        class Fake:
            def tidy(self):
                return pd.DataFrame({"Estimate": [1.0]})

        with pytest.raises(ValueError, match=re.escape("Pr(>|t|), Std. Error")):
            PyFixestExtractor().coef_table(Fake())

    def test_metadata(self, fitted_model, fitted_model_fe):
        e = PyFixestExtractor()
        assert e.depvar(fitted_model) == "y"
        assert e.fixef_string(fitted_model) is None
        assert e.fixef_string(fitted_model_fe) == "group"
        assert e.vcov_info(fitted_model)["vcov_type"] == fitted_model._vcov_type
        assert e.sample_split(fitted_model) is None
        assert e.stat_labels(fitted_model) is None
        assert e.default_stat_keys(fitted_model) is None
        assert e.depvar(types.SimpleNamespace()) == "y"

    def test_stats(self, fitted_model, fitted_model_fe):
        e = PyFixestExtractor()
        assert e.stat(fitted_model, "N") == 100
        assert isinstance(e.stat(fitted_model, "N"), int)
        assert e.stat(fitted_model, "r2") == pytest.approx(fitted_model._r2)
        assert e.stat(fitted_model_fe, "r2_within") == pytest.approx(
            fitted_model_fe._r2_within
        )
        assert e.stat(fitted_model, "bogus") is None
        assert e.stat(fitted_model, "se_type") == fitted_model._vcov_type
        sup = e.supported_stats(fitted_model)
        assert {"N", "r2", "se_type"} <= sup
        assert "r2_within" in sup

    def test_clustered_se_type_and_n_clusters(self, simple_df):
        import pyfixest as pf

        rng = np.random.default_rng(0)
        df = simple_df.copy()
        df["y"] = 2 * df["x"] + rng.standard_normal(len(df))
        m = pf.feols("y ~ x", data=df, vcov={"CRV1": "group"})
        e = PyFixestExtractor()
        assert e.stat(m, "se_type") == "by: group"
        assert e.stat(m, "n_clusters") == 2
        assert e.vcov_info(m)["clustervar"] == ["group"]

    def test_sample_split(self, simple_df):
        import pyfixest as pf

        rng = np.random.default_rng(0)
        df = simple_df.copy()
        df["y"] = 2 * df["x"] + rng.standard_normal(len(df))
        fit = pf.feols("y ~ x", data=df, split="group")
        values = {
            PyFixestExtractor().sample_split(m) for m in fit.all_fitted_models.values()
        }
        assert values == {"A", "B"}

    def test_sample_split_without_value(self):
        m = types.SimpleNamespace(_sample_split_var="g", _sample_split_value=None)
        assert PyFixestExtractor().sample_split(m) is None

    def test_poisson_deviance(self, simple_df):
        import pyfixest as pf

        rng = np.random.default_rng(0)
        df = simple_df.copy()
        df["cnt"] = rng.poisson(3, len(df))
        m = pf.fepois("cnt ~ x", data=df)
        assert PyFixestExtractor().stat(m, "deviance") is not None

    def test_n_fallback_when_not_integer(self):
        assert PyFixestExtractor().stat(types.SimpleNamespace(_N="x"), "N") == "x"

    def test_var_labels(self, fitted_model, monkeypatch):
        e = PyFixestExtractor()
        assert isinstance(e.var_labels(fitted_model), dict)
        assert e.var_labels(types.SimpleNamespace()) is None

        def boom(*a, **k):
            raise RuntimeError

        monkeypatch.setattr(ex, "get_var_labels", boom)
        m = types.SimpleNamespace(_data=pd.DataFrame({"x": [1]}))
        assert e.var_labels(m) is None


# ---------------------------------------------------------------- inspect_model


class TestInspectModel:
    def test_unknown_model_prints_error(self, clean_registry, capsys):
        inspect_model(_Dummy())
        out = capsys.readouterr().out
        assert out.startswith("Error: No extractor available")

    def test_concise_statsmodels(self, statsmodels_logit, capsys):
        inspect_model(statsmodels_logit)
        out = capsys.readouterr().out
        assert "StatsmodelsExtractor" in out
        assert "COEFFICIENT TABLE COLUMNS" in out
        assert "Available: b, se, t, p, ci95l" in out
        assert "pseudo_r2" in out
        assert "Defaults: N, pseudo_r2, ll" in out
        assert "depvar=y_binary" in out
        assert "vcov=nonrobust" in out

    def test_long_statsmodels(self, statsmodels_logit, capsys):
        inspect_model(statsmodels_logit, long=True)
        out = capsys.readouterr().out
        assert "Number of coefficients: 2" in out
        assert "First few rows" in out
        assert "Supported stats" in out
        assert "Default stats (auto-shown in ETable): N, pseudo_r2, ll" in out
        assert "(default)" in out
        assert "Dependent variable: y_binary" in out
        assert "Variance-covariance type: nonrobust" in out
        assert "Fixed effects: None" in out

    def test_pyfixest_clustered_concise_and_long(self, simple_df, capsys):
        import pyfixest as pf

        rng = np.random.default_rng(0)
        df = simple_df.copy()
        df["y"] = 2 * df["x"] + rng.standard_normal(len(df))
        m = pf.feols("y ~ x | group", data=df, vcov={"CRV1": "group"})
        inspect_model(m)
        out = capsys.readouterr().out
        assert "PyFixestExtractor" in out
        assert "vcov=CRV(['group'])" in out
        assert "fixef=group" in out
        inspect_model(m, long=True)
        out = capsys.readouterr().out
        assert "Cluster variable: ['group']" in out
        assert "Fixed effects: group" in out

    def test_linearmodels(self, linearmodels_panelols, capsys):
        inspect_model(linearmodels_panelols)
        out = capsys.readouterr().out
        assert "LinearmodelsExtractor" in out
        assert "fixef=entity" in out

    def test_plugin_with_no_stats_and_errors(self, clean_registry, capsys):
        class Broken:
            __maketables_coef_table__ = "not a frame"

        inspect_model(Broken())
        out = capsys.readouterr().out
        assert "PluginExtractor" in out
        assert "Error: __maketables_coef_table__ must return" in out
        assert "(none)" in out
        assert "depvar=Dependent Variable" in out

        inspect_model(Broken(), long=True)
        out = capsys.readouterr().out
        assert "(no statistics extracted)" in out

    def test_stat_failures_are_tolerated(self, clean_registry, capsys):
        class Ex(_DummyExtractor):
            def coef_table(self, model):
                return pd.DataFrame({"b": [1.0], "empty": [np.nan]}, index=["x"])

            def stat(self, model, key):
                raise RuntimeError

            def default_stat_keys(self, model):
                raise RuntimeError

            def supported_stats(self, model):
                return set()

            def depvar(self, model):
                raise RuntimeError("no depvar")

        register_extractor(Ex())
        inspect_model(_Dummy(), long=True)
        out = capsys.readouterr().out
        assert "b               (1/1 non-null)" in out
        assert "- empty" not in out
        assert "(no statistics extracted)" in out
        assert "Error: no depvar" in out
