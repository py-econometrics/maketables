"""Snapshot tests for ETable (regression tables)."""

import re

import maketables as mt


def normalize_html(html: str) -> str:
    """Normalize HTML output by replacing random IDs with a stable placeholder."""
    # Great Tables generates random 10-char IDs like "pndhlhgcwx"
    # Replace both the id attribute and CSS selectors using that ID
    normalized = re.sub(r'id="([a-z]{10})"', 'id="STABLE_ID"', html)
    normalized = re.sub(r"#[a-z]{10}", "#STABLE_ID", normalized)
    return normalized


class TestETableSnapshots:
    """Snapshot tests for ETable output formats."""

    def test_single_model_html(self, fitted_model, snapshot):
        """Single model ETable HTML output."""
        table = mt.ETable([fitted_model])
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_single_model_latex(self, fitted_model, snapshot):
        """Single model ETable LaTeX output."""
        table = mt.ETable([fitted_model])
        latex = table.make(type="tex")
        assert latex == snapshot

    def test_multi_model_html(self, fitted_models, snapshot):
        """Multi-model ETable HTML output."""
        table = mt.ETable(fitted_models)
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_multi_model_latex(self, fitted_models, snapshot):
        """Multi-model ETable LaTeX output."""
        table = mt.ETable(fitted_models)
        latex = table.make(type="tex")
        assert latex == snapshot

    def test_fixed_effects_html(self, fitted_model_fe, snapshot):
        """Model with fixed effects HTML output."""
        table = mt.ETable([fitted_model_fe])
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_fixed_effects_latex(self, fitted_model_fe, snapshot):
        """Model with fixed effects LaTeX output."""
        table = mt.ETable([fitted_model_fe])
        latex = table.make(type="tex")
        assert latex == snapshot


class TestStatsmodelsSnapshots:
    """Snapshot tests for statsmodels output formats."""

    def test_ols_html(self, statsmodels_ols, snapshot):
        """Statsmodels OLS HTML output."""
        table = mt.ETable([statsmodels_ols])
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_ols_latex(self, statsmodels_ols, snapshot):
        """Statsmodels OLS LaTeX output."""
        table = mt.ETable([statsmodels_ols])
        latex = table.make(type="tex")
        assert latex == snapshot

    def test_logit_html(self, statsmodels_logit, snapshot):
        """Statsmodels Logit HTML output."""
        table = mt.ETable([statsmodels_logit])
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_logit_latex(self, statsmodels_logit, snapshot):
        """Statsmodels Logit LaTeX output."""
        table = mt.ETable([statsmodels_logit])
        latex = table.make(type="tex")
        assert latex == snapshot

    def test_probit_html(self, statsmodels_probit, snapshot):
        """Statsmodels Probit HTML output."""
        table = mt.ETable([statsmodels_probit])
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_probit_latex(self, statsmodels_probit, snapshot):
        """Statsmodels Probit LaTeX output."""
        table = mt.ETable([statsmodels_probit])
        latex = table.make(type="tex")
        assert latex == snapshot


class TestLinearmodelsSnapshots:
    """Snapshot tests for linearmodels output formats."""

    def test_panelols_html(self, linearmodels_panelols, snapshot):
        """Linearmodels PanelOLS HTML output."""
        table = mt.ETable([linearmodels_panelols])
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_panelols_latex(self, linearmodels_panelols, snapshot):
        """Linearmodels PanelOLS LaTeX output."""
        table = mt.ETable([linearmodels_panelols])
        latex = table.make(type="tex")
        assert latex == snapshot

    def test_pooledols_html(self, linearmodels_pooledols, snapshot):
        """Linearmodels PooledOLS HTML output."""
        table = mt.ETable([linearmodels_pooledols])
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_pooledols_latex(self, linearmodels_pooledols, snapshot):
        """Linearmodels PooledOLS LaTeX output."""
        table = mt.ETable([linearmodels_pooledols])
        latex = table.make(type="tex")
        assert latex == snapshot

    def test_absorbingls_html(self, linearmodels_absorbingls, snapshot):
        """Linearmodels AbsorbingLS HTML output."""
        table = mt.ETable([linearmodels_absorbingls])
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_absorbingls_latex(self, linearmodels_absorbingls, snapshot):
        """Linearmodels AbsorbingLS LaTeX output."""
        table = mt.ETable([linearmodels_absorbingls])
        latex = table.make(type="tex")
        assert latex == snapshot

    def test_iv2sls_html(self, linearmodels_iv2sls, snapshot):
        """Linearmodels IV2SLS HTML output."""
        table = mt.ETable([linearmodels_iv2sls])
        html = normalize_html(table.make(type="gt").as_raw_html())
        assert html == snapshot

    def test_iv2sls_latex(self, linearmodels_iv2sls, snapshot):
        """Linearmodels IV2SLS LaTeX output."""
        table = mt.ETable([linearmodels_iv2sls])
        latex = table.make(type="tex")
        assert latex == snapshot
