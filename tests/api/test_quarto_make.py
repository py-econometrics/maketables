"""Tests for MTable.make(type="quarto") dispatch behavior."""

import json

from docx.document import Document as DocxDocument
from great_tables import GT
import maketables as mt
import pandas as pd


def _make_simple_table() -> mt.MTable:
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    return mt.MTable(df)


def _write_quarto_info(tmp_path, base_format=None, target_format=None):
    info = {
        "format": {
            "identifier": {
                "base-format": base_format,
                "target-format": target_format,
            }
        }
    }
    path = tmp_path / "quarto-execute-info.json"
    path.write_text(json.dumps(info), encoding="utf-8")
    return path


def test_make_quarto_falls_back_to_gt_when_env_missing(monkeypatch):
    monkeypatch.delenv("QUARTO_EXECUTE_INFO", raising=False)

    result = _make_simple_table().make(type="quarto")

    assert isinstance(result, GT)


def test_make_quarto_falls_back_to_gt_when_file_missing(monkeypatch, tmp_path):
    missing_path = tmp_path / "missing.json"
    monkeypatch.setenv("QUARTO_EXECUTE_INFO", str(missing_path))

    result = _make_simple_table().make(type="quarto")

    assert isinstance(result, GT)


def test_make_quarto_uses_html_when_quarto_base_is_html(monkeypatch, tmp_path):
    info_path = _write_quarto_info(tmp_path, base_format="html", target_format="html")
    monkeypatch.setenv("QUARTO_EXECUTE_INFO", str(info_path))

    result = _make_simple_table().make(type="quarto")

    assert isinstance(result, str)
    assert "<table" in result.lower()


def test_make_quarto_uses_tex_when_quarto_base_is_latex(monkeypatch, tmp_path):
    info_path = _write_quarto_info(
        tmp_path, base_format="latex", target_format="pdf"
    )
    monkeypatch.setenv("QUARTO_EXECUTE_INFO", str(info_path))

    result = _make_simple_table().make(type="quarto")

    assert isinstance(result, str)
    assert "\\begin{threeparttable}" in result


def test_make_quarto_uses_typst_when_quarto_base_is_typst(monkeypatch, tmp_path):
    info_path = _write_quarto_info(
        tmp_path, base_format="typst", target_format="typst"
    )
    monkeypatch.setenv("QUARTO_EXECUTE_INFO", str(info_path))

    result = _make_simple_table().make(type="quarto")

    assert isinstance(result, str)
    assert "#table(" in result


def test_make_quarto_uses_docx_when_quarto_base_is_docx(monkeypatch, tmp_path):
    info_path = _write_quarto_info(tmp_path, base_format="docx", target_format="docx")
    monkeypatch.setenv("QUARTO_EXECUTE_INFO", str(info_path))

    result = _make_simple_table().make(type="quarto")

    assert isinstance(result, DocxDocument)


def test_make_quarto_uses_target_format_when_base_missing(monkeypatch, tmp_path):
    info_path = _write_quarto_info(tmp_path, base_format=None, target_format="html")
    monkeypatch.setenv("QUARTO_EXECUTE_INFO", str(info_path))

    result = _make_simple_table().make(type="quarto")

    assert isinstance(result, str)
    assert "<table" in result.lower()


def test_make_quarto_prefers_typst_target_over_latex_base(monkeypatch, tmp_path):
    info_path = _write_quarto_info(
        tmp_path, base_format="latex", target_format="typst"
    )
    monkeypatch.setenv("QUARTO_EXECUTE_INFO", str(info_path))

    result = _make_simple_table().make(type="quarto")

    assert isinstance(result, str)
    assert "#table(" in result


def test_make_quarto_falls_back_to_gt_for_unknown_format(monkeypatch, tmp_path):
    info_path = _write_quarto_info(tmp_path, base_format="gfm", target_format="gfm")
    monkeypatch.setenv("QUARTO_EXECUTE_INFO", str(info_path))

    result = _make_simple_table().make(type="quarto")

    assert isinstance(result, GT)


def test_dtable_constructor_accepts_type_quarto(monkeypatch, tmp_path):
    info_path = _write_quarto_info(tmp_path, base_format="latex", target_format="pdf")
    monkeypatch.setenv("QUARTO_EXECUTE_INFO", str(info_path))

    df = pd.DataFrame({"x": [1.0, 2.0, 3.0], "g": ["a", "a", "b"]})
    table = mt.DTable(df, vars=["x"], stats=["mean"], bycol=["g"], type="quarto")
    result = table.make(type="quarto")

    assert isinstance(result, str)
    assert "\\begin{threeparttable}" in result
