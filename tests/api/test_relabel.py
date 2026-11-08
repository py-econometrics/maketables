"""Tests for relabeling coefficient names (categoricals and interactions)."""

import pytest

from maketables.etable import _relabel_expvar

TEMPLATE = "{variable}={value}"


@pytest.mark.parametrize(
    ("varname", "expected"),
    [
        # formulaic/patsy C() notation
        ("C(c)[T.B]", "Country=B"),
        ("C(c)[B]:x", "Country=B * Size"),
        ("C(c, contr.treatment(base='A'))[T.B]", "Country=B"),
        ("C(c, contr.treatment(base='a:b'))[T.B]:x", "Country=B * Size"),
        ("C(c)[T.B]:C(f2)[T.Y]", "Country=B * f2=Y"),
        # variable that is categorical at the outset
        ("cat[T.B]", "cat=B"),
        # pyfixest i() notation (newer pyfixest versions)
        ("c::B", "Country=B"),
        ("c::B:x", "Country=B * Size"),
        ("x:c::B", "Size * Country=B"),
        ("c::A:f2::Y", "Country=A * f2=Y"),
        ("rel::-2", "rel=-2"),
        # plain variables and interactions
        ("x", "Size"),
        ("x:z", "Size * z"),
        ("Intercept", "Intercept"),
        ("np.log(x)", "np.log(x)"),
        # levels containing ":", "::", "[" or "]"
        ("C(t)[T.10:30]", "t=10:30"),
        ("C(t)[T.10:30]:x", "t=10:30 * Size"),
        ("C(o)[T.a[1]]", "o=a[1]"),
        ("cat[T.a::b]", "cat=a::b"),
        ("o::a[1]", "o=a[1]"),
        ("o::a[1]:x", "o=a[1] * Size"),
    ],
)
def test_relabel_expvar(varname, expected):
    labels = {"c": "Country", "x": "Size"}
    assert _relabel_expvar(varname, labels, " * ", TEMPLATE) == expected


def test_relabel_expvar_no_template_keeps_double_colon():
    assert _relabel_expvar("c::B:x", {}, " * ") == "c::B * x"


def test_relabel_expvar_value_int():
    assert _relabel_expvar("fl::2.0", {}, " * ", "{variable}={value_int}") == "fl=2"
