"""The S.E. type row: from the "se_type" stat, else built from vcov_info()."""

import pandas as pd
import pytest

import maketables as mt


class _Result:
    """Minimal plug-in result object."""

    def __init__(self, stats=None, vcov_info=None):
        self._stats = stats or {}
        if vcov_info is not None:
            self.__maketables_vcov_info__ = vcov_info

    @property
    def __maketables_coef_table__(self):
        return pd.DataFrame({"b": [0.5], "se": [0.1], "p": [0.01]}, index=["x"])

    def __maketables_stat__(self, key):
        return self._stats.get(key)


def _se_type_cell(result):
    df = mt.ETable([result], model_stats=["se_type"]).df
    return df.loc[("stats", "S.E. type")].iloc[0]


@pytest.mark.parametrize(
    ("vcov_info", "expected"),
    [
        ({"vcov_type": "hetero"}, "hetero"),
        ({"vcov_type": "CRV1", "clustervar": "firm"}, "by: firm"),
        ({"vcov_type": "CRV1", "clustervar": ["firm", "year"]}, "by: firm+year"),
        ({}, "-"),
        (None, "-"),
    ],
)
def test_se_type_falls_back_to_vcov_info(vcov_info, expected):
    assert _se_type_cell(_Result(vcov_info=vcov_info)) == expected


def test_se_type_stat_takes_precedence_over_vcov_info():
    result = _Result(stats={"se_type": "iid"}, vcov_info={"vcov_type": "hetero"})
    assert _se_type_cell(result) == "iid"


def test_se_type_unchanged_for_pyfixest(fitted_model):
    assert _se_type_cell(fitted_model) == "iid"
