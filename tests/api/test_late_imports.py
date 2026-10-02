"""Model packages installed after maketables was imported must still work.

Typical case: a notebook imports maketables for descriptives, then installs
pyfixest via pip and fits models in the same session. Each test runs in a
fresh interpreter in which the model package is unimportable while
maketables is imported, and only becomes importable afterwards.
"""

import subprocess
import sys
import textwrap

import pytest

_SCRIPT = """
import sys

class _Block:
    def find_spec(self, name, path=None, target=None):
        if name == {package!r} or name.startswith({package!r} + "."):
            raise ImportError("blocked: " + name)

blocker = _Block()
sys.meta_path.insert(0, blocker)
import maketables as mt
assert {package!r} not in sys.modules
sys.meta_path.remove(blocker)

import numpy as np
import pandas as pd

{fit}
print(mt.ETable([model]).make(type="tex")[:20])
"""

_FIT_PYFIXEST = """
import pyfixest as pf
df = pd.DataFrame({"x": np.arange(20.0), "y": np.arange(20.0) ** 1.5})
model = pf.feols("y ~ x", data=df)
"""

_FIT_LINEARMODELS = """
from linearmodels.iv import IV2SLS
df = pd.DataFrame({"x": np.arange(20.0), "y": np.arange(20.0) ** 1.5})
df["const"] = 1.0
model = IV2SLS(df["y"], df[["const", "x"]], None, None).fit()
"""


@pytest.mark.parametrize(
    ("package", "fit"),
    [("pyfixest", _FIT_PYFIXEST), ("linearmodels", _FIT_LINEARMODELS)],
)
def test_package_imported_after_maketables(package, fit):
    pytest.importorskip(package)
    script = _SCRIPT.format(package=package, fit=textwrap.dedent(fit))
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
