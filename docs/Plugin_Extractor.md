# Plug-in Extractor Format Specification

## Overview

This specification defines how external packages can make their model classes compatible with `maketables` without requiring modifications to the `maketables` codebase itself (such as adding a specific extractor). A package simply needs to implement a standardized set of attributes and methods on its model result classes.

## Required Implementation

### 1. Coefficient Table DataFrame

Add a property or attribute named `__maketables_coef_table__` to your model result class:

```python
@property
def __maketables_coef_table__(self) -> pd.DataFrame:
    """
    Return a DataFrame with regression coefficients and statistics.
    
    Required columns:
    - 'b': coefficient estimates
    - 'se': standard errors
    - 't': t-statistics
    - 'p': p-values
    
    Optional columns:
    - 'ci95l', 'ci95u': 95% confidence interval bounds
    - 'ci90l', 'ci90u': 90% confidence interval bounds
    
    Returns
    -------
    pd.DataFrame
        Index: coefficient names (str)
        Columns: canonical column names (str)
        Values: numeric (float or int)
    """
    # Your implementation here
    coef_table = pd.DataFrame({
        'b': self.params,
        'se': self.bse,
        't': self.tvalues,
        'p': self.pvalues,
    })
    coef_table.index.name = 'Coefficient'
    return coef_table
```

### 2. Model Statistics Dictionary

Add a method named `__maketables_stat__` to your model result class:

```python
def __maketables_stat__(self, key: str) -> float | str | int | None:
    """
    Return a model statistic by key.
    
    Common keys:
    - 'N': number of observations
    - 'r2': R-squared
    - 'adj_r2': adjusted R-squared
    - 'r2_within': within R-squared (panel models)
    - 'r2_between': between R-squared (panel models)
    - 'll': log-likelihood
    - 'aic': Akaike information criterion
    - 'bic': Bayesian information criterion
    - 'rmse': root mean squared error
    - 'fvalue': F-statistic
    - 'f_pvalue': F-statistic p-value
    - 'se_type': type of standard errors (e.g., 'robust', 'clustered')
    
    Args
    ----
    key : str
        The statistic key to retrieve.
    
    Returns
    -------
    float, str, int, or None
        The statistic value, or None if not available.
    """
    stats = {
        'N': self.nobs,
        'r2': self.rsquared,
        'adj_r2': self.rsquared_adj,
        'aic': self.aic,
        'bic': self.bic,
    }
    return stats.get(key)
```

### 3. Dependent Variable Name (Optional but recommended)

Add a property named `__maketables_depvar__`:

```python
@property
def __maketables_depvar__(self) -> str:
    """
    Return the name of the dependent variable.
    
    Returns
    -------
    str
        Name of the dependent variable (e.g., 'wage', 'log_income').
    """
    return self.model.endog_names  # or however you store this
```

### 4. Fixed Effects String (Optional, for panel/FE models)

Add a property named `__maketables_fixef_string__`:

```python
@property
def __maketables_fixef_string__(self) -> str | None:
    """
    Return a string describing fixed effects, formatted as space-separated variable names.
    
    Returns
    -------
    str or None
        Fixed effects as a '+'-separated string (e.g., 'firm+year'),
        or None if no fixed effects / not applicable.
    """
    if hasattr(self, 'fe_vars'):
        return '+'.join(self.fe_vars)
    return None
```

### 5. Variable Labels Dictionary (Optional)

Add a property named `__maketables_var_labels__`:

```python
@property
def __maketables_var_labels__(self) -> dict[str, str] | None:
    """
    Return a mapping from variable names to human-readable labels.
    
    Returns
    -------
    dict or None
        Mapping like {'wage': 'Log Wage', 'educ': 'Years of Education'}.
        Return None if no labels available.
    """
    # Try to get from attached DataFrame metadata
    if hasattr(self, 'data') and hasattr(self.data, 'attrs'):
        return self.data.attrs.get('variable_labels')
    return None
```

### 6. Variance-Covariance Info (Optional)

Add a property named `__maketables_vcov_info__`:

```python
@property
def __maketables_vcov_info__(self) -> dict[str, str] | None:
    """
    Return information about the variance-covariance matrix / standard error type.
    
    Returns
    -------
    dict or None
        A dictionary with optional keys:
        - 'se_type': e.g., 'iid', 'robust', 'clustered'
        - 'cluster_var': name of clustering variable (if clustered)
        - 'cluster_level': level of clustering (if applicable)
        
        Return None or empty dict if not applicable.
    """
    vcov_info = {}
    if hasattr(self, 'cov_type'):
        vcov_info['se_type'] = self.cov_type
    if hasattr(self, 'cov_kwds'):
        if 'groups' in self.cov_kwds:
            vcov_info['cluster_var'] = 'clustered'
    return vcov_info if vcov_info else None
```

## How maketables Detects and Uses These

maketables will check for these attributes in order:

1. **Check for `__maketables_coef_table__`** → If found, use it as the coefficient table
2. **Check for `__maketables_stat__` method** → If found, call it for requested statistics
3. **Check for `__maketables_depvar__`** → If found, use as dependent variable label
4. **Check for `__maketables_fixef_string__`** → If found, use for fixed effects panel
5. **Check for `__maketables_var_labels__`** → If found, use for variable relabeling
6. **Check for `__maketables_vcov_info__`** → If found, use for SE type information

If a model class implements these standards, maketables will automatically use it without any additional extractor code.

## Implementation Example: A Hypothetical Package

```python
# mymodels/results.py

import pandas as pd

class MyRegressionResult:
    """A regression result object from the 'mymodels' package."""
    
    def __init__(self, params, bse, tvalues, pvalues, nobs, rsquared, 
                 depvar_name, data=None):
        self.params = params
        self.bse = bse
        self.tvalues = tvalues
        self.pvalues = pvalues
        self.nobs = nobs
        self.rsquared = rsquared
        self._depvar_name = depvar_name
        self.data = data
    
    @property
    def __maketables_coef_table__(self):
        """Standard maketables coefficient table."""
        return pd.DataFrame({
            'b': self.params,
            'se': self.bse,
            't': self.tvalues,
            'p': self.pvalues,
        })
    
    def __maketables_stat__(self, key: str):
        """Standard maketables statistics access."""
        stats = {
            'N': self.nobs,
            'r2': self.rsquared,
        }
        return stats.get(key)
    
    @property
    def __maketables_depvar__(self):
        """Standard maketables dependent variable."""
        return self._depvar_name
```

Then in your package:

```python
# mymodels/__init__.py
from .results import MyRegressionResult

# Users can now do:
from mymodels import MyRegressionResult
from maketables import ETable

result = MyRegressionResult(...)
table = ETable(result)  # Works out of the box!
```
