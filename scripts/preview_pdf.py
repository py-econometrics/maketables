r"""Render one or more maketables tables to PDF in every requested output format.

A quick way to visually check a table across tex/typst/docx while working on
a rendering feature, instead of manually wrapping/compiling each format by
hand. Requires external tools to actually produce PDFs (see --formats below);
any tool that isn't found on PATH is skipped with a warning, not an error.

Usage
-----
Write a small script that defines either a `table` variable or a `TABLES`
dict of {name: table}, e.g.:

    import pyfixest as pf
    import maketables as mt

    est = pf.feols("y ~ x", data=df)
    table = mt.ETable([est], model_heads=["Line one\\nLine two"])

Then run:

    pixi run -e dev preview-pdf my_script.py
    pixi run -e dev preview-pdf my_script.py --formats tex,typst
    pixi run -e dev preview-pdf my_script.py --output-dir ./out

Requires (only for the formats you actually want a PDF for):
    tex   - a LaTeX distribution providing pdflatex on PATH
    typst - the typst CLI (installed automatically in the `dev` pixi env)
    docx  - LibreOffice (`soffice` on PATH) or Microsoft Word (Windows only)
    html  - no PDF conversion is attempted; the raw .html is saved for you
            to open directly in a browser (fully interactive, no conversion
            needed) - unless --combine is passed, in which case a headless
            Chrome/Edge screenshot is used instead (see --combine below).

--combine additionally writes {name}_combined.pdf per table: every
requested format's output as its own labelled page (or pages), so you can
flip through all of them at once. Requires `pymupdf` (installed in the
`dev` pixi env) to build the combined file, and a headless-capable
Chrome/Edge on PATH to include an HTML page (skipped with a warning if
either is missing).
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ALL_FORMATS = ["tex", "typst", "docx", "html"]
FORMAT_LABELS = {
    "tex": "TEX",
    "typst": "TYPST",
    "docx": "DOCX",
    "html": "HTML (screenshot)",
}

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


def load_tables(script_path: Path) -> dict[str, object]:
    """Load the `table` variable or `TABLES` dict from a user-supplied script."""
    spec = importlib.util.spec_from_file_location("preview_target", script_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load script: {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, "TABLES"):
        return dict(module.TABLES)
    if hasattr(module, "table"):
        return {"table": module.table}
    raise SystemExit(
        "Script must define a `table` variable or a `TABLES` dict of {name: table}."
    )


def render_tex(table, out_dir: Path, name: str) -> Path | None:
    """Compile the table's tex output to PDF via pdflatex, if available."""
    tex_path = out_dir / f"{name}.tex"
    tex_path.write_text(
        TEX_PREAMBLE + table.make(type="tex") + TEX_POSTAMBLE, encoding="utf-8"
    )

    pdflatex = shutil.which("pdflatex")
    if pdflatex is None:
        print(
            f"  [tex]   skipped (pdflatex not found on PATH) -> wrote {tex_path.name}"
        )
        return None

    result = subprocess.run(
        [pdflatex, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
        cwd=out_dir,
        capture_output=True,
        text=True,
    )
    for ext in ("aux", "log"):
        (out_dir / f"{name}.{ext}").unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"  [tex]   FAILED to compile {tex_path.name} (see output below)")
        print(result.stdout[-2000:])
        return None
    final_pdf = out_dir / f"{name}_tex.pdf"
    final_pdf.unlink(missing_ok=True)
    (out_dir / f"{name}.pdf").rename(final_pdf)
    print(f"  [tex]   -> {final_pdf.name}")
    return final_pdf


def render_typst(table, out_dir: Path, name: str) -> Path | None:
    """Compile the table's typst output to PDF via the typst CLI, if available."""
    typ_path = out_dir / f"{name}.typ"
    typ_path.write_text(table.make(type="typst"), encoding="utf-8")

    typst = shutil.which("typst")
    if typst is None:
        print(
            f"  [typst] skipped (typst CLI not found on PATH) -> wrote {typ_path.name}"
        )
        return None

    pdf_path = out_dir / f"{name}_typst.pdf"
    result = subprocess.run(
        [typst, "compile", typ_path.name, pdf_path.name],
        cwd=out_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  [typst] FAILED to compile {typ_path.name} (see output below)")
        print(result.stderr[-2000:])
        return None
    print(f"  [typst] -> {pdf_path.name}")
    return pdf_path


def render_html(table, out_dir: Path, name: str) -> Path | None:
    """Save the table's gt/html output as a standalone .html file (no PDF conversion)."""
    html_path = out_dir / f"{name}.html"
    body = table.make(type="gt").as_raw_html()
    doc = (
        "<html><head><meta charset='utf-8'></head>"
        "<body style='padding:40px;font-family:sans-serif;'>" + body + "</body></html>"
    )
    html_path.write_text(doc, encoding="utf-8")
    print(
        f"  [html]  -> {name}.html (open directly in a browser; no PDF conversion attempted)"
    )
    return html_path


def render_docx(table, out_dir: Path, name: str) -> Path | None:
    """Convert the table's docx output to PDF via LibreOffice or Microsoft Word."""
    docx_path = out_dir / f"{name}.docx"
    table.save(type="docx", file_name=str(docx_path), replace=True)
    final_pdf = out_dir / f"{name}_docx.pdf"

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice is not None:
        result = subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(out_dir),
                str(docx_path),
            ],
            capture_output=True,
            text=True,
        )
        # LibreOffice always names its output after the input file's stem.
        produced = out_dir / f"{name}.pdf"
        if result.returncode == 0 and produced.exists():
            final_pdf.unlink(missing_ok=True)
            produced.rename(final_pdf)
            print(f"  [docx]  -> {final_pdf.name} (via LibreOffice)")
            return final_pdf
        print(
            "  [docx]  LibreOffice conversion failed, trying Word next (if available)"
        )

    if sys.platform == "win32":
        try:
            import win32com.client

            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            try:
                doc = word.Documents.Open(str(docx_path))
                doc.SaveAs(str(final_pdf), FileFormat=17)  # wdFormatPDF
                doc.Close()
            finally:
                word.Quit()
        except ImportError:
            pass
        except Exception as e:  # Word not installed / COM error
            print(f"  [docx]  Word conversion failed: {e}")
        else:
            print(f"  [docx]  -> {final_pdf.name} (via Microsoft Word)")
            return final_pdf

    print(
        f"  [docx]  skipped PDF conversion (no LibreOffice or Word found) "
        f"-> wrote {docx_path.name}"
    )
    return None


RENDERERS = {
    "tex": render_tex,
    "typst": render_typst,
    "docx": render_docx,
    "html": render_html,
}


def find_browser() -> str | None:
    """Locate a headless-capable Chrome/Edge/Chromium binary, if any."""
    for candidate in (
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
        "msedge",
        "chrome",
    ):
        found = shutil.which(candidate)
        if found:
            return found
    for path in (
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ):
        if Path(path).exists():
            return path
    return None


def capture_html_screenshot(html_path: Path, out_dir: Path, name: str) -> Path | None:
    """Screenshot the rendered HTML via headless Chrome/Edge, autocropping whitespace."""
    browser = find_browser()
    if browser is None:
        print("  [combine] skipped HTML page (no Chrome/Edge/Chromium found)")
        return None

    png_path = out_dir / f"{name}_html.png"
    result = subprocess.run(
        [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--window-size=1400,2000",
            f"--screenshot={png_path}",
            html_path.resolve().as_uri(),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not png_path.exists():
        print(f"  [combine] HTML screenshot failed: {result.stderr[-500:]}")
        return None

    try:
        from PIL import Image, ImageChops

        img = Image.open(png_path).convert("RGB")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bbox = ImageChops.difference(img, bg).getbbox()
        if bbox:
            img.crop(bbox).save(png_path)
    except Exception:
        pass  # autocrop is a nicety, not worth failing over
    return png_path


def build_combined_pdf(
    results: dict[str, Path | None], out_dir: Path, name: str
) -> None:
    """Combine each format's output into one PDF, with a labelled page before each."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print(
            "  [combine] skipped (pymupdf not installed; it's part of the `dev` "
            "pixi env - run `pixi install -e dev`)"
        )
        return

    combined = fitz.open()
    for fmt in ALL_FORMATS:
        path = results.get(fmt)
        if path is None or not path.exists():
            continue

        label_page = combined.new_page(width=595, height=120)
        label_page.insert_text(
            fitz.Point(40, 75), FORMAT_LABELS[fmt], fontsize=28, fontname="helv"
        )

        if path.suffix.lower() == ".pdf":
            with fitz.open(str(path)) as src:
                combined.insert_pdf(src)
        else:  # image (the HTML screenshot)
            with fitz.open(str(path)) as img:
                rect = img[0].rect
                page = combined.new_page(width=rect.width, height=rect.height)
                page.insert_image(rect, filename=str(path))

    if combined.page_count == 0:
        print("  [combine] nothing to combine (no format produced output)")
        combined.close()
        return

    combined_path = out_dir / f"{name}_combined.pdf"
    combined.save(str(combined_path))
    combined.close()
    print(f"  [combine] -> {combined_path.name}")


def main() -> None:
    """Parse CLI args, load the target table(s), and render each requested format."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "script", type=Path, help="Python file defining `table` or `TABLES`"
    )
    parser.add_argument(
        "--formats",
        default=",".join(ALL_FORMATS),
        help=f"Comma-separated subset of {ALL_FORMATS} (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("preview_output"),
        help="Directory to write outputs into (default: ./preview_output)",
    )
    parser.add_argument(
        "--combine",
        action="store_true",
        help="Also write {name}_combined.pdf, with each requested format as "
        "its own labelled page(s) (requires pymupdf; HTML requires a "
        "headless-capable Chrome/Edge)",
    )
    args = parser.parse_args()

    formats = [f.strip() for f in args.formats.split(",") if f.strip()]
    unknown = set(formats) - set(ALL_FORMATS)
    if unknown:
        raise SystemExit(
            f"Unknown format(s): {sorted(unknown)}. Choose from {ALL_FORMATS}."
        )

    tables = load_tables(args.script)
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, table in tables.items():
        print(f"{name}:")
        results: dict[str, Path | None] = {}
        for fmt in formats:
            results[fmt] = RENDERERS[fmt](table, out_dir, name)

        if args.combine:
            html_path = results.get("html")
            if "html" in formats and html_path is not None:
                results["html"] = capture_html_screenshot(html_path, out_dir, name)
            build_combined_pdf(results, out_dir, name)

    print(f"\nDone. Output in {out_dir}")


if __name__ == "__main__":
    main()
