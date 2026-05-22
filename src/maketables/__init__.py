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
