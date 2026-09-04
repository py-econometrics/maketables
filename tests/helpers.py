"""Shared test utilities for maketables snapshot tests."""

import re


def normalize_html(html: str) -> str:
    """Normalize HTML output by replacing random IDs with a stable placeholder."""
    html = html.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r'id="([a-z]{10})"', 'id="STABLE_ID"', html)
    normalized = re.sub(r"#[a-z]{10}", "#STABLE_ID", normalized)
    return normalized


def normalize_typst(typst: str) -> str:
    """Normalize Typst output for stable cross-platform snapshotting."""
    return typst.replace("\r\n", "\n").replace("\r", "\n")


def normalize_latex(tex: str) -> str:
    """Normalize LaTeX output for stable cross-platform snapshotting."""
    return tex.replace("\r\n", "\n").replace("\r", "\n")
