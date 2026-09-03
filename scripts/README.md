# scripts/

Maintainer-only dev tooling. Not part of the shipped package, not run by CI or
the test suite - invoke directly or via the matching `pixi run -e dev` task.

- `preview_pdf.py` (`pixi run -e dev preview-pdf`) - render a table to PDF
  across all output formats (tex/typst/docx/html) for visually checking a
  rendering feature. See the script's docstring for usage.
