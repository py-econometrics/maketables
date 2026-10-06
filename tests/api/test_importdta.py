import warnings

import pandas as pd
import pytest

from maketables import MTable
from maketables.importdta import export_dta, get_var_labels, import_dta, set_var_labels


@pytest.fixture(autouse=True)
def _restore_default_labels():
    saved = dict(MTable.DEFAULT_LABELS)
    yield
    MTable.DEFAULT_LABELS = saved


@pytest.fixture
def df():
    return pd.DataFrame(
        {
            "price": [10.0, 20.0, 30.0, 40.0],
            "mpg": [1, 2, 3, 4],
            "origin": pd.Categorical(["a", "b", "a", "b"]),
        }
    )


@pytest.fixture
def dta(tmp_path, df):
    path = tmp_path / "x.dta"
    df.to_stata(
        path,
        write_index=False,
        variable_labels={"price": "Price in USD", "mpg": "Miles per gallon"},
    )
    return path


def test_import_basic(dta):
    out = import_dta(dta)
    assert out.attrs["variable_labels"] == {
        "price": "Price in USD",
        "mpg": "Miles per gallon",
    }
    assert isinstance(out["origin"].dtype, pd.CategoricalDtype)


def test_import_no_attrs_and_return_labels(dta):
    out, labels = import_dta(dta, store_in_attrs=False, return_labels=True)
    assert "variable_labels" not in out.attrs
    assert labels["mpg"] == "Miles per gallon"


def test_import_str_path(dta):
    assert len(import_dta(str(dta))) == 4


def test_import_no_categoricals(dta):
    out = import_dta(dta, convert_categoricals=False)
    assert not isinstance(out["origin"].dtype, pd.CategoricalDtype)


def test_import_update_defaults_fill_and_override(dta):
    MTable.DEFAULT_LABELS = {"price": "Mine"}
    import_dta(dta, update_mtable_defaults=True)
    assert MTable.DEFAULT_LABELS["price"] == "Mine"
    assert MTable.DEFAULT_LABELS["mpg"] == "Miles per gallon"
    import_dta(dta, update_mtable_defaults=True, override=True)
    assert MTable.DEFAULT_LABELS["price"] == "Price in USD"


def test_import_typeerror_fallback(dta, monkeypatch):
    import maketables.importdta as mod

    real = mod.StataReader

    def fake(path, **kwargs):
        if kwargs:
            raise TypeError("unsupported")
        return real(path)

    monkeypatch.setattr(mod, "StataReader", fake)
    out = import_dta(dta)
    assert out.attrs["variable_labels"]["price"] == "Price in USD"


def test_export_roundtrip_priority(tmp_path, df):
    MTable.DEFAULT_LABELS = {"price": "default", "mpg": "default mpg", "zzz": "n/a"}
    df.attrs["variable_labels"] = {"price": "attr", "origin": "Origin"}
    path = tmp_path / "o.dta"
    export_dta(df, path, labels={"origin": "explicit", "nocol": "x"}, data_label="d")
    _, labels = import_dta(path, return_labels=True)
    assert labels == {"price": "attr", "mpg": "default mpg", "origin": "explicit"}


def test_export_no_defaults_no_attrs(tmp_path, df):
    MTable.DEFAULT_LABELS = {"price": "default"}
    df.attrs["variable_labels"] = {"mpg": "attr"}
    path = tmp_path / "o.dta"
    export_dta(df, path, use_defaults=False, use_df_attrs=False)
    _, labels = import_dta(path, return_labels=True)
    assert labels == {}


def test_export_exists_and_overwrite(tmp_path, df):
    path = tmp_path / "o.dta"
    export_dta(df, path)
    with pytest.raises(FileExistsError):
        export_dta(df, path)
    export_dta(df, path, overwrite=True, labels={"price": "New"})
    assert import_dta(path, return_labels=True)[1]["price"] == "New"


def test_export_truncates_long_label(tmp_path, df):
    path = tmp_path / "o.dta"
    with pytest.warns(RuntimeWarning, match="exceeds 80"):
        export_dta(df, path, labels={"price": "x" * 100})
    assert import_dta(path, return_labels=True)[1]["price"] == "x" * 80


def test_export_typeerror_fallback(tmp_path, df, monkeypatch):
    calls = []
    real = pd.DataFrame.to_stata

    def fake(self, path, **kwargs):
        calls.append(kwargs)
        if "variable_labels" in kwargs:
            raise TypeError("nope")
        return real(self, path, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "to_stata", fake)
    with pytest.warns(RuntimeWarning, match="variable_labels"):
        export_dta(df, tmp_path / "o.dta", labels={"price": "P"})
    assert len(calls) == 2
    assert (tmp_path / "o.dta").exists()


def test_get_var_labels(df):
    assert get_var_labels(df) == {}
    df.attrs["variable_labels"] = {"price": "P", "mpg": None}
    MTable.DEFAULT_LABELS = {"mpg": "M", "price": "ignored", "other": "o"}
    assert get_var_labels(df) == {"price": "P"}
    assert get_var_labels(df, include_defaults=True) == {"price": "P", "mpg": "M"}


def test_set_var_labels_overwrite_and_skip_missing(df):
    out = set_var_labels(df, {"price": "P", "nocol": "x"})
    assert out == {"price": "P"}
    out = set_var_labels(df, {"price": "P2", "mpg": None}, overwrite=False)
    assert out == {"price": "P", "mpg": None}
    assert df.attrs["variable_labels"] is out


def test_set_var_labels_update_defaults(df):
    MTable.DEFAULT_LABELS = {"price": "old"}
    df2 = df.copy()
    set_var_labels(df, {"price": "P", "mpg": "M"}, update_mtable_defaults=True)
    assert MTable.DEFAULT_LABELS == {"price": "P", "mpg": "M"}

    MTable.DEFAULT_LABELS = {"price": "old"}
    set_var_labels(
        df2,
        {"price": "P", "mpg": "M"},
        overwrite=False,
        update_mtable_defaults=True,
    )
    assert MTable.DEFAULT_LABELS == {"price": "old", "mpg": "M"}


def test_export_long_string_uses_strl(tmp_path):
    long = "y" * 3000
    out = pd.DataFrame({"s": [long, "short"], "n": [1, 2]})
    path = tmp_path / "long.dta"
    export_dta(out, path)
    assert import_dta(path)["s"].tolist() == [long, "short"]


def test_no_warnings_on_normal_roundtrip(tmp_path, df):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        export_dta(df, tmp_path / "o.dta", labels={"price": "P"})
