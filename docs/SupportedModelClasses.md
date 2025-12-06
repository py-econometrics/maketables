# Supported Model Classes

`maketables` supports creating regression tables for models from currently the following packages: 

- [PyFixest](https://github.com/py-econometrics/pyfixest)
- [Statsmodels](https://github.com/statsmodels/statsmodels)
- [Linearmodels](https://github.com/bashtage/linearmodels)
- [Stata](https://www.stata.com/python/pystata19/) (see [documentation](pystataIntegration.ipynb))

<br>
<br>
<br>

# Adding Support for New Packages

There are two ways to make a statistical package compatible with `ETables` in `maketables` for automatic table generation:

- *Custom Extractor Implementation:* Implement a custom extractor following the `ModelExtractor` protocol and register it in `maketables/extractors.py`. This approach requires code changes to maketables itself.

- *Plug-in Extractor Format:*: If you want your package to work with maketables out of the box, implement a few standard attributes and methods on your model result class (`__maketables_coef_table__`, `__maketables_stat__`, etc.). 

See [Adding Methods](AddingMethods.ipynb) for a guide on implementing either of the two approaches.
