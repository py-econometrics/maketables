# ruff: noqa: SLF001, FBT003
import numpy as np
import pandas as pd
import pytest

pytest.importorskip("ipywidgets")
pytest.importorskip("pyfixest")

import maketables.interactive as inter
from maketables.interactive import (
    InteractiveDTable,
    InteractiveFeols,
    _construct_formula,
    _parse_formula,
    interactive_dtable,
    interactive_regression,
)


@pytest.fixture
def data():
    rng = np.random.default_rng(0)
    n = 120
    return pd.DataFrame(
        {
            "y": rng.normal(size=n),
            "x1": rng.normal(size=n),
            "x2": rng.normal(size=n),
            "grp": rng.choice(["a", "b", "c"], size=n),
            "g2": rng.integers(0, 4, size=n),
        }
    )


@pytest.fixture
def shown(monkeypatch):
    """Capture objects passed to display() instead of rendering."""
    items = []
    monkeypatch.setattr(inter, "display", items.append)
    return items


def test_parse_formula():
    assert _parse_formula("y ~ x1 + x2 | a + b") == ("y", ["x1", "x2"], ["a", "b"])
    assert _parse_formula("y ~ x1") == ("y", ["x1"], [])


def test_parse_formula_invalid():
    with pytest.raises(ValueError, match="exactly one"):
        _parse_formula("y x1")
    with pytest.raises(ValueError, match="exactly one"):
        _parse_formula("y ~ x ~ z")


def test_construct_formula():
    assert _construct_formula("y", ["x1", "x2"], ["a"]) == "y ~ x1 + x2 | a"
    assert _construct_formula("y", ["x1"], []) == "y ~ x1"
    assert _construct_formula("y", ["x1"], ["None"]) == "y ~ x1"
    with pytest.raises(ValueError, match="At least one"):
        _construct_formula("y", [], [])


def test_feols_bad_formula(data):
    with pytest.raises(ValueError, match="Error parsing"):
        InteractiveFeols(data, "y x1")


def test_feols_widgets(data):
    w = InteractiveFeols(data, "y ~ x1 | grp", vcov="HC1")
    assert w.numeric_vars == ["y", "x1", "x2", "g2"]
    assert w.categorical_vars == ["grp"]
    assert w.depvar_widget.value == "y"
    assert w.vcov_widget.value == "HC1"
    assert w.fixef_widget.value == ("grp",)
    assert "g2" in w.fixef_widget.options
    w2 = InteractiveFeols(data, "grp ~ x1", vcov="bogus")
    assert w2.depvar_widget.value == "y"  # non-numeric depvar falls back
    assert w2.vcov_widget.value == "iid"
    assert w2.fixef_widget.value == ("None",)


def test_feols_generate_code(data):
    w = InteractiveFeols(data, "y ~ x1")
    w._generate_code("y ~ x1", "hetero", None)
    assert "vcov='hetero'" in w.code_widget.value
    assert "fml='y ~ x1'" in w.code_widget.value
    w._generate_code("y ~ x1", {"CRV1": "grp"}, "grp")
    assert "vcov={'CRV1': 'grp'}" in w.code_widget.value
    w._generate_code("y ~ x1", "iid", "None")
    assert "vcov='iid'" in w.code_widget.value


def test_feols_display_and_update(data, shown):
    w = interactive_regression(data, "y ~ x1 + x2", show_code=True, title="T")
    assert isinstance(w, InteractiveFeols)
    assert shown[0].children[0].value == "<h3>T</h3>"
    assert "pf.feols" in w.code_widget.value

    w.cluster_widget.value = "grp"
    assert "CRV1" in w.code_widget.value
    w.cluster_widget.value = "None"
    w.vcov_widget.value = "HC3"
    assert "vcov='HC3'" in w.code_widget.value


def test_feols_update_no_indepvars_and_error(data, shown, capsys):
    w = InteractiveFeols(data, "y ~ x1")
    w.display()
    w.indepvars_widget.value = ()
    assert "at least one independent" in capsys.readouterr().out
    w.indepvars_widget.value = ("x1",)
    w.data = data.drop(columns=["x1"])
    w._update_results()
    assert "Error" in capsys.readouterr().out


def test_feols_no_code_by_default(data, shown):
    w = InteractiveFeols(data, "y ~ x1")
    w.display()
    assert w.code_widget.value == ""


def test_dtable_defaults(data):
    w = InteractiveDTable(data)
    assert w.initial_vars == ["y", "x1", "x2", "g2"]
    assert w.bycol_widget.value == ("None",)
    assert "grp" in w.byrow_widget.options
    w2 = InteractiveDTable(data, initial_vars=["y"])
    assert w2.vars_widget.value == ("y",)


def test_dtable_generate_code_variants(data):
    w = InteractiveDTable(data)
    w._generate_code(["y", "x1"], ["mean"], None, None, 2, False, False)
    code = w.code_widget.value
    assert "vars=['y', 'x1']" in code
    assert "bycol" not in code
    assert "format_spec" not in code
    w._generate_code(["y"], ["mean", "std"], ["grp"], "g2", 4, True, True)
    code = w.code_widget.value
    assert "bycol=['grp']" in code
    assert "byrow='g2'" in code
    assert "'mean': '.4f'" in code
    assert "'var': '.5f'" in code
    assert "hide_stats=True" in code
    assert "counts_row_below=True" in code


def test_dtable_display_and_update(data, shown):
    w = interactive_dtable(data, vars=["y", "x1"], show_code=True, title="Title")
    assert isinstance(w, InteractiveDTable)
    assert shown[0].children[0].value == "<h3>Title</h3>"
    assert "mt.DTable" in w.code_widget.value

    w.bycol_widget.value = ("grp",)
    assert "bycol=['grp']" in w.code_widget.value
    w.byrow_widget.value = "g2"
    w.digits_widget.value = 3
    w.hide_stats_widget.value = True
    w.counts_row_below_widget.value = True
    assert "byrow='g2'" in w.code_widget.value


def test_dtable_update_empty_selections_and_error(data, shown, capsys):
    w = InteractiveDTable(data)
    w.display()
    w.vars_widget.value = ()
    assert "at least one variable" in capsys.readouterr().out
    w.vars_widget.value = ("y",)
    w.stats_widget.value = ()
    assert "at least one statistic" in capsys.readouterr().out
    w.stats_widget.value = ("mean",)
    w.data = data.drop(columns=["y"])
    w._update_results()
    assert "Error" in capsys.readouterr().out
