"""Base snapshot tests for linearmodels models."""

import re

import maketables as mt


def normalize_html(html: str) -> str:
    """Normalize HTML output by replacing random IDs with a stable placeholder."""
    normalized = re.sub(r'id="([a-z]{10})"', 'id="STABLE_ID"', html)
    normalized = re.sub(r"#[a-z]{10}", "#STABLE_ID", normalized)
    return normalized


class TestLinearmodels:
    """Base tests for linearmodels model extraction."""

    def test_panelols_html(self, linearmodels_panelols, snapshot):
        """Linearmodels PanelOLS HTML output."""
        table = mt.ETable([linearmodels_panelols])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_panelols_latex(self, linearmodels_panelols, snapshot):
        """Linearmodels PanelOLS LaTeX output."""
        table = mt.ETable([linearmodels_panelols])
        assert table.make(type="tex") == snapshot

    def test_pooledols_html(self, linearmodels_pooledols, snapshot):
        """Linearmodels PooledOLS HTML output."""
        table = mt.ETable([linearmodels_pooledols])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_pooledols_latex(self, linearmodels_pooledols, snapshot):
        """Linearmodels PooledOLS LaTeX output."""
        table = mt.ETable([linearmodels_pooledols])
        assert table.make(type="tex") == snapshot

    def test_absorbingls_html(self, linearmodels_absorbingls, snapshot):
        """Linearmodels AbsorbingLS HTML output."""
        table = mt.ETable([linearmodels_absorbingls])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_absorbingls_latex(self, linearmodels_absorbingls, snapshot):
        """Linearmodels AbsorbingLS LaTeX output."""
        table = mt.ETable([linearmodels_absorbingls])
        assert table.make(type="tex") == snapshot

    def test_iv2sls_html(self, linearmodels_iv2sls, snapshot):
        """Linearmodels IV2SLS HTML output."""
        table = mt.ETable([linearmodels_iv2sls])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_iv2sls_latex(self, linearmodels_iv2sls, snapshot):
        """Linearmodels IV2SLS LaTeX output."""
        table = mt.ETable([linearmodels_iv2sls])
        assert table.make(type="tex") == snapshot
