"""Layered tests for the tex/typst/docx/PDF output formats.

Each format is tested at the most stable layer available instead of diffing
compiled artifacts byte-for-byte:
- typst/tex: snapshot the generated source directly.
- docx: snapshot a python-docx extraction (cell text), not the .docx file.
- PDF: a compile smoke test (pass/fail) plus a pdfplumber text-content
  snapshot, skipped when the required CLI (pdflatex/typst) isn't on PATH -
  these are dev-only checks, not something CI is required to provide.
"""

import shutil
import subprocess

import pytest
from helpers import normalize_typst

import maketables as mt

HAS_PDFLATEX = shutil.which("pdflatex") is not None
HAS_TYPST = shutil.which("typst") is not None

TEX_PREAMBLE = (
    "\\documentclass{article}\n"
    "\\usepackage{booktabs}\n"
    "\\usepackage{makecell}\n"
    "\\usepackage{tabularx}\n"
    "\\usepackage{threeparttable}\n"
    "\\usepackage[margin=1in]{geometry}\n"
    "\\usepackage{amssymb}\n"
    "\\pagestyle{empty}\n"
    "\\begin{document}\n"
)
TEX_POSTAMBLE = "\n\\end{document}\n"


def docx_table_text(document) -> list[list[list[str]]]:
    """Extract each table's cell text, ignoring run-level styling."""
    return [
        [[cell.text for cell in row.cells] for row in table.rows]
        for table in document.tables
    ]


def pdf_text(pdf_path) -> str:
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


class TestTypstOutput:
    """Layer 2/4 tests for the typst renderer."""

    def test_typst_snapshot(self, fitted_model, snapshot):
        """Snapshot the generated typst source."""
        table = mt.ETable([fitted_model])
        assert normalize_typst(table.make(type="typst")) == snapshot

    @pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not found on PATH")
    def test_typst_compiles(self, fitted_model, tmp_path):
        """Compile smoke test: the typst CLI accepts the generated source."""
        table = mt.ETable([fitted_model])
        typ_path = tmp_path / "out.typ"
        typ_path.write_text(table.make(type="typst"), encoding="utf-8")

        result = subprocess.run(
            ["typst", "compile", typ_path.name, "out.pdf"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        pdf_path = tmp_path / "out.pdf"
        assert pdf_path.stat().st_size > 0

    @pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not found on PATH")
    def test_typst_pdf_content(self, fitted_model, tmp_path, snapshot):
        """Snapshot the text extracted from the compiled typst PDF."""
        table = mt.ETable([fitted_model])
        typ_path = tmp_path / "out.typ"
        typ_path.write_text(table.make(type="typst"), encoding="utf-8")
        subprocess.run(
            ["typst", "compile", typ_path.name, "out.pdf"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True,
        )
        assert pdf_text(tmp_path / "out.pdf") == snapshot


class TestLatexPdfOutput:
    """Layer 4 tests for the LaTeX renderer: compile smoke test + PDF content."""

    @pytest.mark.skipif(not HAS_PDFLATEX, reason="pdflatex not found on PATH")
    def test_latex_compiles(self, fitted_model, tmp_path):
        """Compile smoke test: pdflatex accepts the generated tex source."""
        table = mt.ETable([fitted_model])
        tex_path = tmp_path / "out.tex"
        tex_path.write_text(
            TEX_PREAMBLE + table.make(type="tex") + TEX_POSTAMBLE, encoding="utf-8"
        )

        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout[-2000:]
        pdf_path = tmp_path / "out.pdf"
        assert pdf_path.stat().st_size > 0

    @pytest.mark.skipif(not HAS_PDFLATEX, reason="pdflatex not found on PATH")
    def test_pdf_content(self, fitted_model, tmp_path, snapshot):
        """Snapshot the text extracted from the compiled LaTeX PDF."""
        table = mt.ETable([fitted_model])
        tex_path = tmp_path / "out.tex"
        tex_path.write_text(
            TEX_PREAMBLE + table.make(type="tex") + TEX_POSTAMBLE, encoding="utf-8"
        )
        subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=True,
        )
        assert pdf_text(tmp_path / "out.pdf") == snapshot


class TestDocxOutput:
    """Layer 3 tests for the docx renderer."""

    def test_docx_table_content(self, fitted_model, tmp_path, snapshot):
        """Snapshot a python-docx extraction of the table's cell text."""
        table = mt.ETable([fitted_model])
        docx_path = tmp_path / "out.docx"
        table.save(type="docx", file_name=str(docx_path), replace=True)

        import docx

        document = docx.Document(str(docx_path))
        assert docx_table_text(document) == snapshot
