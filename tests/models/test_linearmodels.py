"""Base snapshot tests for linearmodels models."""

import maketables as mt
from helpers import normalize_html


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
