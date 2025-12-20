"""Shared test utilities for maketables snapshot tests."""

import re


def normalize_html(html: str) -> str:
    """Normalize HTML output by replacing random IDs with a stable placeholder."""
    normalized = re.sub(r'id="([a-z]{10})"', 'id="STABLE_ID"', html)
    normalized = re.sub(r"#[a-z]{10}", "#STABLE_ID", normalized)
    return normalized
