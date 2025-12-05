# Supported Model Classes

`maketables` supports creating regression tables for models from currently the following packages: 

- [PyFixest](https://github.com/py-econometrics/pyfixest)
- [Statsmodels](https://github.com/statsmodels/statsmodels)
- [Linearmodels](https://github.com/bashtage/linearmodels)
- [Stata](https://www.stata.com/python/pystata19/) via [PyStata](docs\pystataIntegration.ipynb)



## Adding Support for New Packages

There are two ways to make your package compatible with `maketables`:



### 1. **Plug-in Extractor Format** 

If you maintain a statistical modeling package, you can make your model result classes compatible with `maketables` **without any code changes to `maketables`**. Simply implement a few standard attributes and methods on your model class:

- `__maketables_coef_table__` (property): Returns a DataFrame with coefficient estimates and statistics
- `__maketables_stat__(key)` (method): Returns model statistics by key
- `__maketables_depvar__` (property): Returns the dependent variable name

This approach has **no external dependencies** — your package never imports `maketables`. Users can then use your models directly with `ETable()`:

```python
from mypackage import MyRegression
from maketables import ETable

result = MyRegression(y, X)
table = ETable(result)  # Works automatically!
```

**See [Plugin Extractor Format](../PLUGIN_EXTRACTOR_FORMAT.md) for complete specifications.**



### 2. **Custom Extractor Implementation** (For Core Integration)

If instead the package itself should not be changed, implement a custom extractor (such as maketables has for instance for statsmodels, PyFixest, or linearmodels) that follows the `ModelExtractor` protocol and register it in `maketables/extractors.py`.

This approach requires implementing the extractor interface including:
- `can_handle(model)`: Detect your model type
- `coef_table(model)`: Extract coefficients
- `stat(model, key)`: Extract statistics
- Additional extraction (depvar, fixed effects, variable labels, etc.)

**See [Adding Methods](AddingMethods.ipynb) for a detailed guide on implementing a custom extractor.**
