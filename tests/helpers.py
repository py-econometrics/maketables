"""Shared test utilities for maketables snapshot tests."""

import re

import pytest

OUTPUT_TYPES = [
    pytest.param("gt", id="html"),
    pytest.param("tex", id="latex"),
    pytest.param("typst", id="typst"),
]


def normalize_html(html: str) -> str:
    """Normalize HTML output by replacing random IDs with a stable placeholder."""
    html = html.replace("\r\n", "\n").replace("\r", "\n")
    html = re.sub(r'id="([a-z]{10})"', 'id="STABLE_ID"', html)
    return re.sub(r"#[a-z]{10}", "#STABLE_ID", html)


def render_table(table, output_type: str) -> str:
    """Render a table and normalize HTML snapshots."""
    rendered = table.make(type=output_type)
    if output_type == "gt":
        return normalize_html(rendered.as_raw_html())
    return rendered


def normalize_typst(typst: str) -> str:
    """Normalize Typst output for stable cross-platform snapshotting."""
    return typst.replace("\r\n", "\n").replace("\r", "\n")


def normalize_latex(tex: str) -> str:
    """Normalize LaTeX output for stable cross-platform snapshotting."""
    return tex.replace("\r\n", "\n").replace("\r", "\n")
