# MakeTables

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/license/mit)
![Python Versions](https://img.shields.io/badge/Python-3.9–3.14-blue)
[![PyPI -Version](https://img.shields.io/pypi/v/maketables.svg)](https://pypi.org/project/maketables/)
[![Known Bugs](https://img.shields.io/github/issues/py-econometrics/maketables/bug?color=red&label=Bugs)](https://github.com/py-econometrics/maketables/issues?q=is%3Aissue+is%3Aopen+label%3Abug)
[![File an Issue](https://img.shields.io/github/issues/py-econometrics/maketables)](https://github.com/py-econometrics/maketables/issues)
[![Downloads](https://static.pepy.tech/badge/maketables)](https://pepy.tech/project/maketables)
[![Downloads](https://static.pepy.tech/badge/maketables/month)](https://pepy.tech/project/maketables)
[![PyPI](https://img.shields.io/pypi/v/maketables)](https://pypi.org/project/maketables)

[Docs](https://py-econometrics.github.io/maketables/docs/getting-started.html) · [Function & API Reference](https://py-econometrics.github.io/maketables/reference/) · [Report Bugs & Request Features](https://github.com/py-econometrics/maketables/issues) · [Adding Support for new Model Classes](https://py-econometrics.github.io/maketables/docs/AddingMethods.html)

A Python package for creating publication-ready tables from regression results (`statsmodels`, `pyfixest`, `linearmodels`), descriptive statistics, and balance tables with output to *LaTeX*, *Word*, *HTML* and *Typst* via [Great Tables](https://github.com/posit-dev/great-tables). To get started, check out the [Getting Started Notebook](https://py-econometrics.github.io/maketables/docs/getting-started.html).

## Overview

MakeTables provides a unified interface for generating tables such as:

- Regression tables from [Statsmodels](https://www.statsmodels.org/stable/index.html), [PyFixest](https://py-econometrics.github.io/pyfixest/pyfixest.html), [Linearmodels](https://bashtage.github.io/linearmodels/) and [Stata](https://www.stata.com/python/pystata19/)
- Descriptive statistics 
- Balance tables

The package supports multiple output formats including:

- *Great Tables (HTML)*
- *LaTeX*
- *Microsoft Word (docx)* documents
- *Typst*

## Model Support

`maketables` supports creating regression tables for models from the following packages: 

- [PyFixest](https://github.com/py-econometrics/pyfixest)
- [statsmodels](https://github.com/statsmodels/statsmodels)
- [linearmodels](https://github.com/bashtage/linearmodels)
- [lifelines](https://github.com/CamDavidsonPilon/lifelines)

## Origin

MakeTables originated as the table output functionality within the [pyfixest](https://github.com/py-econometrics/pyfixest) package and has been moved to this standalone package to provide broader table creation capabilities also supporting other statistical packages.

## Authors

- Alexander Fischer [https://github.com/s3alfischer](https://github.com/s3alfisc)
- Dirk Sliwka [https://dsliwka.github.io/](https://dsliwka.github.io)

## Installation

### From PyPI
```bash
pip install maketables
```

### Development Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/maketables.git
cd maketables

# Install in development mode
pip install -e .
```

## Quick Start

### Descriptive Statistics Table

```python
import pandas as pd
import maketables as mt

# Load your data (here using a sample Stata dataset with the import_dta function that also stores variable labels)
df = mt.import_dta("https://www.stata-press.com/data/r18/auto.dta")


# Create descriptive statistics table
mt.DTable(df, vars=["mpg","weight","length"], bycol=["foreign"])
```

### Regression Tables

#### with pyfixest
```python
import pyfixest as pf

# Fit your models here using pyfixest
est1 = pf.feols("mpg ~ weight", data=df)
est2 = pf.feols("mpg ~ weight + length", data=df)

# Make the table
mt.ETable([est1, est2])
```

#### with statsmodels
```python
import statsmodels.formula.api as smf

# Generate a dummy variable and label it
df["foreign_i"] = (df["foreign"] == "Foreign")*1
mt.set_var_labels(df, {"foreign_i": "Foreign (indicator)"})

# Fit your models 
est1 = smf.ols("foreign_i ~ weight + length + price", data=df).fit()
est2 = smf.probit("foreign_i ~ weight + length + price", data=df).fit(disp=0)

# Make the table
mt.ETable([est1, est2], model_stats=["N","r2","pseudo_r2",""], model_heads=["OLS","Probit"])
```


## Main Classes

### `MTable`
Base class for all table types with common functionality:
- Multiple output formats (Great Tables, LaTeX, Word)
- Flexible styling and formatting options
- Save and export capabilities
- Can also update tables in existing word documents
- Adapted for use in Jupyter Notebooks and for quarto use (tables automatically rendered as html in notebooks and as latex when rendering to pdf in quarto)


### `DTable`
Extends MTable for descriptive statistics:
- Automatic calculation of summary statistics
- Grouping by categorical variables (rows and columns)
- Customizable statistic labels and formatting

### `ETable`
Extends MTable for econometric model results:
- Support for statsmodels, pyfixest, and (more experimental) linearmodels 
- Many layout options (relabelling of variables, keep/drop, choice of reported statistics, column headings,...)

### `BTable`
Extends MTable for simple balance tables.


## License

This project is licensed under the MIT License - see the LICENSE file for details.


## Acknowledgments

- Built on the excellent [pyfixest](https://github.com/py-econometrics/pyfixest) package for econometric models. We gratefully acknowledge the contributors to pyfixest's etable: [@s3alfisc](https://github.com/s3alfisc),
[@dsliwka](https://github.com/dsliwka), [@Wenzhi-Ding](https://github.com/Wenzhi-Ding),
[@juanitorduz](https://github.com/juanitorduz), [@NKeleher](https://github.com/NKeleher),
[@blucap](https://github.com/blucap), [@mortizm1988](https://github.com/mortizm1988),
[@jsr-p](https://github.com/jsr-p), [@IshwaraHegde97](https://github.com/IshwaraHegde97),
[@Erica-Ryan](https://github.com/Erica-Ryan), [@Dpananos](https://github.com/Dpananos),
and [@AronNemeth](https://github.com/AronNemeth).
- Uses [Great Tables](https://github.com/posit-dev/great-tables) for beautiful HTML table output