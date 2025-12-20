"""Base snapshot tests for statsmodels models."""

import maketables as mt
from helpers import normalize_html


class TestStatsmodels:
    """Base tests for statsmodels model extraction."""

    def test_ols_html(self, statsmodels_ols, snapshot):
        """Statsmodels OLS HTML output."""
        table = mt.ETable([statsmodels_ols])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_ols_latex(self, statsmodels_ols, snapshot):
        """Statsmodels OLS LaTeX output."""
        table = mt.ETable([statsmodels_ols])
        assert table.make(type="tex") == snapshot

    def test_logit_html(self, statsmodels_logit, snapshot):
        """Statsmodels Logit HTML output."""
        table = mt.ETable([statsmodels_logit])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_logit_latex(self, statsmodels_logit, snapshot):
        """Statsmodels Logit LaTeX output."""
        table = mt.ETable([statsmodels_logit])
        assert table.make(type="tex") == snapshot

    def test_probit_html(self, statsmodels_probit, snapshot):
        """Statsmodels Probit HTML output."""
        table = mt.ETable([statsmodels_probit])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_probit_latex(self, statsmodels_probit, snapshot):
        """Statsmodels Probit LaTeX output."""
        table = mt.ETable([statsmodels_probit])
        assert table.make(type="tex") == snapshot
