import json, pathlib

nb = {
 "cells": [
  {
   "cell_type": "raw",
   "id": "a1b2c3d4",
   "metadata": {"vscode": {"languageId": "raw"}},
   "source": [
    "---\ntitle: Quarto and MakeTables\nformat:\n  pdf:\n    include-in-header:\n      - text: |\n          \\usepackage{setspace}\n          \\usepackage{float}\n          \\usepackage{booktabs}\n          \\usepackage{makecell}\n          \\usepackage{threeparttable}\n          \\usepackage{tabularx}\n          \\usepackage{multirow}\n          \\usepackage{array}\n    output-file: quartoExampleViaLatex.pdf\n  typst:\n    output-file: quartoExampleViaTypst.pdf\nexecute:\n  enabled: true\n  echo: false\n  warning: false\n  cache: false\nfreeze: false\nbibliography: references.bib\nauthor:\n  - Peter Pan\ndate: May 2025\ndate-format: long\nabstract: This document illustrates how to use MakeTables.\n---"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "b2c3d4e5",
   "metadata": {},
   "outputs": [],
   "source": [
    "#| echo: false\n#| include: false\n#| eval: true\nimport numpy as np\nimport pandas as pd\nimport pyfixest as pf\nimport maketables as mt\nimport statsmodels.formula.api as smf\ndf = mt.import_dta(\"auto.dta\")"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "d4e5f6a7",
   "metadata": {},
   "source": ["## Some Tables\n\n@tbl-1 shows some descriptive statistics."]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "e5f6a7b8",
   "metadata": {},
   "outputs": [],
   "source": [
    "#| label: tbl-1\n#| tbl-cap: Automotive Data Summary\n#| tbl-pos: H\n#| results: asis\nmt.DTable(df, vars=[\"mpg\",\"weight\",\"price\"], stats=[\"count\",\"mean\",\"std\"], bycol=[\"foreign\"], tex_style={\"first_col_width\": \"3cm\"}, type=\"quarto\").make(type=\"quarto\")"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "f6a7b8c9",
   "metadata": {},
   "source": ["@tbl-2 shows regression results estimated with pyfixest."]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "a7b8c9d0",
   "metadata": {},
   "outputs": [],
   "source": [
    "#| label: tbl-2\n#| tbl-cap: A Regression Table\n#| tbl-pos: H\n#| results: asis\nest1 = pf.feols(\"mpg ~ weight\", data=df)\nest2 = pf.feols(\"mpg ~ weight + length\", data=df)\nmt.ETable([est1, est2], type=\"quarto\").make(type=\"quarto\")"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "b8c9d0e1",
   "metadata": {},
   "source": ["@tbl-3 uses statsmodels to estimate a probit model."]
  },
  {
   "cell_type": "code",
   "execution_count": None,
   "id": "c9d0e1f2",
   "metadata": {},
   "outputs": [],
   "source": [
    "#| label: tbl-3\n#| tbl-cap: A Regression Table Statsmodels\n#| tbl-pos: H\n#| results: asis\ndf[\"foreign_i\"] = (df[\"foreign\"] == \"Foreign\")*1\nmt.set_var_labels(df, {\"foreign_i\": \"Foreign (indicator)\"})\nest1 = smf.ols(\"foreign_i ~ weight + length + price\", data=df).fit()\nest2 = smf.probit(\"foreign_i ~ weight + length + price\", data=df).fit(disp=0)\nmt.ETable([est1, est2], model_stats=[\"N\",\"r2\",\"pseudo_r2\"], model_heads=[\"OLS\",\"Probit\"], type=\"quarto\").make(type=\"quarto\")"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "d0e1f2a3",
   "metadata": {},
   "source": ["## Conclusion\n\nLorem ipsum.\n\n{{< pagebreak >}}\n\n## References\n\n::: {#refs}\n:::"]
  }
 ],
 "metadata": {
  "kernelspec": {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.13.0"}
 },
 "nbformat": 4,
 "nbformat_minor": 5
}

path = pathlib.Path("docs/examples/quartoExample.ipynb")
with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
print("written:", path.stat().st_size)
