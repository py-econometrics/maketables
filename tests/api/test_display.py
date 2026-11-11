"""Tests for the rich display bundle used by Jupyter and Quarto."""

import json

import maketables as mt


def test_mimebundle_contains_every_format(fitted_model):
    table = mt.ETable([fitted_model])
    bundle = table._repr_mimebundle_()

    assert set(bundle) == {"text/html", "text/markdown", "text/latex", "text/typst"}
    assert bundle["text/latex"] == table.make(type="tex")
    assert bundle["text/typst"] == table.make(type="typst")


def test_mimebundle_markdown_holds_raw_latex_and_typst_blocks(fitted_model):
    """Pandoc keeps only the raw block matching the output format."""
    table = mt.ETable([fitted_model])
    markdown = table._repr_mimebundle_()["text/markdown"]

    tex = table.make(type="tex")
    typst = table.make(type="typst")
    assert markdown == f"```{{=latex}}\n{tex}\n```\n\n```{{=typst}}\n{typst}\n```"


def test_mimebundle_same_when_rendered_by_quarto(fitted_model, tmp_path, monkeypatch):
    """Outputs stored during a Quarto render must still work for other targets."""
    table = mt.ETable([fitted_model])
    interactive = table._repr_mimebundle_()

    info = tmp_path / "execute-info.json"
    info.write_text(
        json.dumps(
            {
                "format": {
                    "identifier": {"base-format": "typst", "target-format": "typst"}
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("QUARTO_EXECUTE_INFO", str(info))

    rendered = table._repr_mimebundle_()
    assert set(rendered) == set(interactive)
    assert rendered["text/markdown"] == interactive["text/markdown"]
