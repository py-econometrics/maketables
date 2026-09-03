"""Shared test utilities for maketables snapshot tests."""

import re


def normalize_html(html: str) -> str:
    """Normalize HTML output by replacing random IDs with a stable placeholder."""
    html = html.replace("\r\n", "\n").replace("\r", "\n")
    html = re.sub(r'id="([a-z]{10})"', 'id="STABLE_ID"', html)
    return re.sub(r"#[a-z]{10}", "#STABLE_ID", html)
