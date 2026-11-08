import numpy as np
import pandas as pd
import pytest

import maketables as mt
from maketables.extractors import DuckRegExtractor

pytest.importorskip("duckreg")
duckdb = pytest.importorskip("duckdb")
from duckreg.estimators import DuckRegression  # noqa: E402


@pytest.fixture(scope="module")
def duckreg_data():
    rng = np.random.default_rng(12345)
    n = 2_000
    df = pd.DataFrame(
        {
            "D": rng.choice([0, 1], n),
            "f1": rng.integers(0, 10, n),
            "f2": rng.integers(0, 10, n),
        }
    )
    df["Y"] = df["D"] + df["f1"] + 2 * df["f2"] + rng.normal(size=n)
    return df


@pytest.fixture(scope="module")
def duckreg_models(duckreg_data, tmp_path_factory):
    db = str(tmp_path_factory.mktemp("duckreg") / "data.db")
    conn = duckdb.connect(db)
    conn.execute("CREATE TABLE data AS SELECT * FROM duckreg_data")
    conn.close()

    models = []
    for formula in ("Y ~ D + f1", "Y ~ D + f1 + f2"):
        m = DuckRegression(
            db_name=db,
            table_name="data",
            formula=formula,
            cluster_col="f1",
            n_bootstraps=10,
            seed=42,
        )
        m.fit()
        m.fit_vcov()
        models.append(m)
    return models


class TestDuckReg:
    """Extraction tests for duckreg models."""

    def test_can_handle(self, duckreg_models):
        assert DuckRegExtractor().can_handle(duckreg_models[0])
        assert not DuckRegExtractor().can_handle(object())

    def test_coef_table(self, duckreg_models, duckreg_data):
        coefs = DuckRegExtractor().coef_table(duckreg_models[1])
        assert list(coefs.index) == ["Intercept", "D", "f1", "f2"]
        assert list(coefs.columns) == ["b", "se", "t", "p"]

        design = np.column_stack(
            [np.ones(len(duckreg_data)), duckreg_data[["D", "f1", "f2"]]]
        )
        expected = np.linalg.lstsq(design, duckreg_data["Y"], rcond=None)[0]
        np.testing.assert_allclose(coefs["b"], expected)
        np.testing.assert_allclose(coefs["t"], coefs["b"] / coefs["se"])
        assert ((coefs["p"] >= 0) & (coefs["p"] <= 1)).all()

    def test_metadata(self, duckreg_models, duckreg_data):
        ext = DuckRegExtractor()
        model = duckreg_models[0]
        assert ext.depvar(model) == "Y"
        assert ext.fixef_string(model) is None
        assert ext.stat(model, "N") == len(duckreg_data)
        assert ext.stat(model, "r2") is None
        assert ext.vcov_info(model) == {"vcov_type": "cluster", "clustervar": "f1"}

    def test_etable(self, duckreg_models):
        table = mt.ETable(duckreg_models)
        out = table.make("tex")
        assert "Intercept" in out
        assert "f2" in out
