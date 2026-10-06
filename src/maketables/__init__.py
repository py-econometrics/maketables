"""
maketables: publication-ready tables from regression results and data.

Main classes (all render to HTML, LaTeX, Word and Typst with
``.make(type="gt" | "tex" | "docx" | "typst")`` and save with ``.save(...)``;
the HTML output is created with Great Tables):

- ``ETable``: regression tables from pyfixest, statsmodels, linearmodels,
  lifelines and Stata models, and from any package implementing the plug-in
  format below.
- ``DTable``: descriptive statistics, optionally by groups.
- ``BTable``: balance tables with group differences and p-values.
- ``MTable``: base class for custom tables built from a pandas DataFrame.

Plug-in format: a package makes its own result objects work with ``ETable``,
without importing maketables, by adding ``__maketables_coef_table__`` (a
DataFrame with columns ``b``, ``se``, ``p`` and optionally ``t``, ``ci95l``, ...)
and optionally ``__maketables_stat__(key)``, ``__maketables_depvar__`` and
further ``__maketables_*__`` attributes to its result class. Specification with
a complete example:
https://github.com/py-econometrics/maketables/blob/main/PLUGIN_EXTRACTOR_FORMAT.md

Documentation: https://py-econometrics.github.io/maketables/
"""

from importlib.metadata import PackageNotFoundError, version

from .btable import BTable
from .dtable import DTable
from .etable import ETable
from .extractors import (
    ModelExtractor,
    clear_extractors,
    get_extractor,
    inspect_model,
    register_extractor,
)
from .importdta import export_dta, get_var_labels, import_dta, set_var_labels
from .mtable import MTable

try:
    __version__ = version("maketables")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "PYSTATA_AVAILABLE",
    "BTable",
    "DTable",
    "ETable",
    "MTable",
    "ModelExtractor",
    "StataResultWrapper",
    "clear_extractors",
    "export_dta",
    "extract_current_stata_results",
    "get_extractor",
    "get_var_labels",
    "import_dta",
    "inspect_model",
    "register_extractor",
    "rstata",
    "set_var_labels",
]

# Conditionally import PyStata integration if available
try:
    from .pystata_extractor import (
        PYSTATA_AVAILABLE,
        StataResultWrapper,
        extract_current_stata_results,
        rstata,
    )
except ImportError:
    # PyStata not available, these functions won't be accessible
    PYSTATA_AVAILABLE = False
