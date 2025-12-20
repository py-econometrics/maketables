"""Snapshot tests for ETable model statistics."""

import re

import maketables as mt


def normalize_html(html: str) -> str:
    """Normalize HTML output by replacing random IDs with a stable placeholder."""
    normalized = re.sub(r'id="([a-z]{10})"', 'id="STABLE_ID"', html)
    normalized = re.sub(r"#[a-z]{10}", "#STABLE_ID", normalized)
    return normalized


class TestETableModelStats:
    """Snapshot tests for model_stats variations."""

    def test_model_stats_extended_html(self, fitted_model, snapshot):
        """Extended statistics including adj_r2 and rmse."""
        table = mt.ETable([fitted_model], model_stats=["N", "r2", "adj_r2", "rmse"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_model_stats_extended_latex(self, fitted_model, snapshot):
        """Extended statistics including adj_r2 and rmse."""
        table = mt.ETable([fitted_model], model_stats=["N", "r2", "adj_r2", "rmse"])
        assert table.make(type="tex") == snapshot

    def test_model_stats_minimal_html(self, fitted_model, snapshot):
        """Minimal statistics (only N)."""
        table = mt.ETable([fitted_model], model_stats=["N"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_model_stats_minimal_latex(self, fitted_model, snapshot):
        """Minimal statistics (only N)."""
        table = mt.ETable([fitted_model], model_stats=["N"])
        assert table.make(type="tex") == snapshot

    def test_model_stats_with_se_type_html(self, fitted_model, snapshot):
        """Include standard error type."""
        table = mt.ETable([fitted_model], model_stats=["N", "r2", "se_type"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_model_stats_with_se_type_latex(self, fitted_model, snapshot):
        """Include standard error type."""
        table = mt.ETable([fitted_model], model_stats=["N", "r2", "se_type"])
        assert table.make(type="tex") == snapshot

    def test_model_stats_custom_labels_html(self, fitted_model, snapshot):
        """Custom labels for model statistics."""
        table = mt.ETable(
            [fitted_model],
            model_stats=["N", "r2"],
            model_stats_labels={"N": "Sample Size", "r2": "R-squared"},
        )
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_model_stats_custom_labels_latex(self, fitted_model, snapshot):
        """Custom labels for model statistics."""
        table = mt.ETable(
            [fitted_model],
            model_stats=["N", "r2"],
            model_stats_labels={"N": "Sample Size", "r2": "R-squared"},
        )
        assert table.make(type="tex") == snapshot

    def test_model_stats_aic_bic_html(self, fitted_model, snapshot):
        """Information criteria (AIC, BIC)."""
        table = mt.ETable([fitted_model], model_stats=["N", "aic", "bic"])
        assert normalize_html(table.make(type="gt").as_raw_html()) == snapshot

    def test_model_stats_aic_bic_latex(self, fitted_model, snapshot):
        """Information criteria (AIC, BIC)."""
        table = mt.ETable([fitted_model], model_stats=["N", "aic", "bic"])
        assert table.make(type="tex") == snapshot
