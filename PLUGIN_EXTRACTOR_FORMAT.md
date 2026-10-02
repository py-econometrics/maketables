# maketables Plug-in Format

Make the result objects of your own statistics package work with
[maketables](https://github.com/py-econometrics/maketables) regression tables
(`maketables.ETable`) by adding a few `__maketables_*__` attributes to your result
class. Your package does **not** need to import or depend on maketables, and
maketables needs no code changes: it detects these attributes at runtime.

Real-world example: [ModernDiD](https://github.com/jordandeklerk/moderndid)
implements this format for all its difference-in-differences results (see its
[publication tables guide](https://moderndid.readthedocs.io/en/latest/user_guide/publication_tables.html)).

## Minimal example

```python
import pandas as pd


class MyResult:
    """Result object of a hypothetical estimator in your package."""

    def __init__(self, params, se, tvalues, pvalues, nobs, depvar):
        self.params, self.se = params, se
        self.tvalues, self.pvalues = tvalues, pvalues
        self.nobs, self.depvar = nobs, depvar

    # Required: one row per coefficient, canonical column names.
    @property
    def __maketables_coef_table__(self) -> pd.DataFrame:
        return pd.DataFrame(
            {"b": self.params, "se": self.se, "t": self.tvalues, "p": self.pvalues}
        )

    # Optional: model statistics by key; return None for unknown keys.
    def __maketables_stat__(self, key: str):
        return {"N": self.nobs, "se_type": "iid"}.get(key)

    # Optional: name of the dependent variable (column header).
    @property
    def __maketables_depvar__(self) -> str:
        return self.depvar
```

Usage, from the user's side:

```python
import maketables as mt

res = MyResult(
    params=pd.Series({"Intercept": 1.2, "x": 0.5}),
    se=pd.Series({"Intercept": 0.3, "x": 0.1}),
    tvalues=pd.Series({"Intercept": 4.0, "x": 5.0}),
    pvalues=pd.Series({"Intercept": 0.001, "x": 0.0001}),
    nobs=100,
    depvar="y",
)
mt.ETable([res], model_stats=["N", "se_type"])  # HTML in notebooks
mt.ETable([res]).make("tex")                     # also "docx", "typst"
```

## How detection works

`ETable` looks up an extractor for each model. Built-in extractors handle
pyfixest, statsmodels, linearmodels and lifelines; any other object that has a
`__maketables_coef_table__` attribute is handled by the plug-in extractor. Check
with `maketables.get_extractor(res)`, which returns a `PluginExtractor` instance
for plug-in objects, and `maketables.inspect_model(res)`, which prints what
maketables reads from the object.

## Attributes

Only `__maketables_coef_table__` is required; all others are optional and fall
back to the default shown.

| Attribute | Kind | Returns | Default if missing |
|---|---|---|---|
| `__maketables_coef_table__` | property | `pd.DataFrame`, see below | required |
| `__maketables_stat__(key)` | method | value of the statistic `key` (number or str), or `None` if not available | all statistics shown as `-` |
| `__maketables_depvar__` | property | `str`, dependent variable name | `"Dependent Variable"` |
| `__maketables_fixef_string__` | property | fixed effects as a `"+"`-separated `str` (e.g. `"firm+year"`), or `None` | no fixed-effects rows |
| `__maketables_var_labels__` | property | `dict[str, str]` mapping variable names to display labels, or `None` | names shown as-is |
| `__maketables_stat_labels__` | property | `dict[str, str]` mapping statistic keys to display labels, or `None` | built-in labels (below) |
| `__maketables_default_stat_keys__` | property | `list[str]` of statistic keys to show when the user passes no `model_stats` | `["N", "r2"]` |
| `__maketables_vcov_info__` | property | `dict` with variance metadata (e.g. `{"se_type": "cluster", "cluster_var": "firm"}`), or `None` | `{}`; currently informational only, to show the S.E. type in the table return it from `__maketables_stat__("se_type")` |

Labels passed by the user to `ETable` (`labels=`, `model_stats_labels=`) always
take precedence over labels from the model.

### `__maketables_coef_table__`

- **Index:** coefficient names (`str`). These are the row labels; users can
  relabel, `keep`, `drop` and reorder them by name.
- **Columns:** `b` (estimate), `se` (standard error) and `p` (p-value) are used
  by the default cell format `"b:.3f* \n (se:.3f)"`; `p` is also needed for
  significance stars. `t` (test statistic) is optional.
- **Any further numeric columns** become available as tokens in `ETable`'s
  `coef_fmt`, e.g. `ci95l`/`ci95u` for confidence intervals:
  `ETable([res], coef_fmt="b:.3f* \n [ci95l:.3f, ci95u:.3f]")`.

### Statistic keys

`__maketables_stat__` may support any keys; users request them via
`ETable(model_stats=[...])`. These keys have built-in display labels:

| Key | Label | Key | Label |
|---|---|---|---|
| `N` | Observations | `ll` | Log-likelihood |
| `n_clusters` | Clusters | `llnull` | Null log-likelihood |
| `events` | Events | `aic` | AIC |
| `se_type` | S.E. type | `bic` | BIC |
| `r2` | R² | `df_model` | df(model) |
| `adj_r2` | Adj. R² | `df_resid` | df(resid) |
| `r2_within` | Within R² | `deviance` | Deviance |
| `r2_between` | Between R² | `null_deviance` | Null deviance |
| `adj_r2_within` | Within Adj. R² | `concordance` | Concordance |
| `pseudo_r2` | Pseudo R² | `fvalue` | F statistic |
| `rmse` | RMSE | `f_pvalue` | F p-value |
| `fstat_1st` | First-stage F | | |

Other keys are shown with the key as label unless you provide one via
`__maketables_stat_labels__`. Integers and floats are formatted by maketables;
strings are shown as-is.

## Alternative: a registered extractor

If you cannot add attributes to the result class (e.g. for a third-party
package), implement the `maketables.ModelExtractor` protocol in a separate class
and register it with `maketables.register_extractor(MyExtractor())`. See the
[documentation on adding model classes](https://py-econometrics.github.io/maketables/docs/AddingModelClasses.html)
for both approaches in detail.
