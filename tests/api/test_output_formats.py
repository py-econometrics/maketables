"""Layered tests for the tex/typst/docx/PDF output formats.

Each format is tested at the most stable layer available instead of diffing
compiled artifacts byte-for-byte:
- typst/tex: snapshot the generated source directly.
- docx: snapshot a python-docx extraction (cell and paragraph text), not the
  .docx file.
- PDF: a compile smoke test (pass/fail) plus a pdfplumber text-content
  snapshot, skipped when the required CLI (pdflatex/typst) isn't on PATH -
  these are dev-only checks, not something CI is required to provide.

All layers run against the ``sample_table`` fixture family from conftest.py
(ETable, DTable and BTable variants), so each renderer sees plain, multi-model,
formatted, merged-header and wide tables.
"""

import shutil
import subprocess

import pytest
from helpers import normalize_latex, normalize_typst

import maketables as mt

HAS_PDFLATEX = shutil.which("pdflatex") is not None
HAS_TYPST = shutil.which("typst") is not None

needs_pdflatex = pytest.mark.skipif(
    not HAS_PDFLATEX, reason="pdflatex not found on PATH"
)
needs_typst = pytest.mark.skipif(not HAS_TYPST, reason="typst CLI not found on PATH")

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


def docx_paragraph_text(document) -> list[str]:
    """Extract non-empty body paragraphs (caption, notes), ignoring styling."""
    return [p.text for p in document.paragraphs if p.text.strip()]


def pdf_text(pdf_path) -> str:
    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def compile_typst(table, tmp_path, *, check):
    """Write the table's typst source to tmp_path and compile it to out.pdf."""
    typ_path = tmp_path / "out.typ"
    typ_path.write_text(table.make(type="typst"), encoding="utf-8")
    return subprocess.run(
        ["typst", "compile", typ_path.name, "out.pdf"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=check,
    )


def compile_pdflatex(table, tmp_path, *, check):
    """Wrap the table's tex source in a document and compile it to out.pdf."""
    tex_path = tmp_path / "out.tex"
    tex_path.write_text(
        TEX_PREAMBLE + table.make(type="tex") + TEX_POSTAMBLE, encoding="utf-8"
    )
    return subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=check,
    )


class TestTypstOutput:
    """Layer 2/4 tests for the typst renderer."""

    def test_typst_snapshot(self, sample_table, snapshot):
        """Snapshot the generated typst source."""
        assert normalize_typst(sample_table.make(type="typst")) == snapshot

    @needs_typst
    def test_typst_compiles(self, sample_table, tmp_path):
        """Compile smoke test: the typst CLI accepts the generated source."""
        result = compile_typst(sample_table, tmp_path, check=False)
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "out.pdf").stat().st_size > 0

    @needs_typst
    def test_typst_pdf_content(self, sample_table, tmp_path, snapshot):
        """Snapshot the text extracted from the compiled typst PDF."""
        compile_typst(sample_table, tmp_path, check=True)
        assert pdf_text(tmp_path / "out.pdf") == snapshot


class TestLatexOutput:
    """Layer 2/4 tests for the LaTeX renderer."""

    def test_tex_snapshot(self, sample_table, snapshot):
        """Snapshot the generated LaTeX source."""
        assert normalize_latex(sample_table.make(type="tex")) == snapshot

    @needs_pdflatex
    def test_latex_compiles(self, sample_table, tmp_path):
        """Compile smoke test: pdflatex accepts the generated tex source."""
        result = compile_pdflatex(sample_table, tmp_path, check=False)
        assert result.returncode == 0, result.stdout[-2000:]
        assert (tmp_path / "out.pdf").stat().st_size > 0


class TestLatexPdfOutput:
    """Layer 4 PDF-content snapshot for the LaTeX renderer (needs pdflatex)."""

    @needs_pdflatex
    def test_pdf_content(self, fitted_model, tmp_path, snapshot):
        """Snapshot the text extracted from the compiled LaTeX PDF."""
        compile_pdflatex(mt.ETable([fitted_model]), tmp_path, check=True)
        assert pdf_text(tmp_path / "out.pdf") == snapshot


class TestDocxOutput:
    """Layer 3 tests for the docx renderer."""

    def test_docx_content(self, sample_table, tmp_path, snapshot):
        """Snapshot a python-docx extraction of table cells and caption/notes."""
        docx_path = tmp_path / "out.docx"
        sample_table.save(type="docx", file_name=str(docx_path), replace=True)

        import docx

        document = docx.Document(str(docx_path))
        assert {
            "tables": docx_table_text(document),
            "paragraphs": docx_paragraph_text(document),
        } == snapshot
