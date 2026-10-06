# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Adjusted R² was always missing for pyfixest models: the extractor read `_r2_adj`, but pyfixest 0.60 exposes `_adj_r2` (the old name is kept as a fallback)
- linearmodels panel models (`PanelOLS`, `PooledOLS`, ...) showed no S.E. type: these results only expose the private `_cov_type`, which the extractor now falls back to
- `BTable(group=[...])` returned `nan` p-values with recent pyfixest versions (seen with 0.60): the helper column for the joint group test was named with leading double underscores, which pyfixest silently drops from `i()` terms, so the test ran on an intercept-only model

### Added
- **Plug-in specification** [`PLUGIN_EXTRACTOR_FORMAT.md`](https://github.com/py-econometrics/maketables/blob/main/PLUGIN_EXTRACTOR_FORMAT.md): all `__maketables_*__` attributes, coefficient-table columns, statistic keys and a runnable example. The "No extractor available" error now links to it.
- `llms.txt` on the documentation site and a package docstring (`help(maketables)`) to help coding agents find and use maketables and its plug-in interface

### Changed
- Invalid arguments now raise `ValueError` (or `TypeError` for a non-list level in a nested `model_heads`) instead of `AssertionError`: `head_order`, `stats_order`, `model_heads`, `BTable` `group` and `byrow`, and the output `type`. Code catching `AssertionError` for these needs updating
- Development tooling: Ruff with `select = ["ALL"]`, type checking with [ty](https://github.com/astral-sh/ty) instead of mypy, more pre-commit hooks, and a CI matrix over Python 3.10-3.14 on Linux, macOS and Windows. Snapshot tests pin `great-tables==0.18.*` in the pixi dev environments only; the published requirement is still `great-tables>=0.2`
- The development dependency on pyfixest is no longer capped at `<0.31`, which also makes the Python 3.14 environment installable (pyfixest wheels for 3.14 start at 0.40.0, SciPy's at 1.16.1)
- The "S.E. type" row falls back to the model's `vcov_info()` (`vcov_type`, `clustervar`) when the extractor or plug-in returns no `se_type` statistic. Plug-ins can now provide the S.E. type via `__maketables_vcov_info__`; lifelines and Stata models show their S.E. type instead of "-" when `se_type` is requested.

## [0.1.9] - 2026-10-02

### Added
- **Line breaks in labels, headers, and notes**: `"\n"` in variable labels, model headers, column spanners, row-group names, and notes now renders as a line break in all output formats (HTML, LaTeX, Typst, Word)
- **Multi-level model headers**: `ETable(model_heads=...)` accepts a list of levels to stack several header rows
- **Sample-split headers**: pyfixest models estimated with `split`/`fsplit` get their sample as model header automatically
- **Statistics ordering**: new `ETable(stats_order=...)` sets the order of custom and model statistics in the bottom panel, or hides either block
- **Fixed-effects ordering**: new `ETable(feorder=...)` sets the order of fixed-effect rows
- **BTable row groups**: new `BTable(byrow=...)` splits a balance table into row groups
- **BTable list-valued groups**: `BTable(group=[...])` accepts several grouping variables
- **Dev script** `scripts/preview_pdf.py` (`pixi run -e dev preview-pdf`) previews a table as PDF across output formats

### Changed
- `DTable`/`BTable` no longer show a standard deviation for binary variables in combined statistics

### Fixed
- **Models from packages installed after importing maketables**: pyfixest and linearmodels models raised `TypeError: No extractor available for model type: Feols` when the package was installed (or first became importable) after maketables had already been imported, e.g. `pip install pyfixest` midway through a Colab notebook. Their model classes are now looked up when a model is checked instead of once at import time.
- **great_tables >= 1.0 compatibility**: Line breaks in body cells, row labels, and row-group labels (e.g. the coefficient / standard-error cells of `ETable`) rendered as literal `<br>` text with great_tables 1.0, which now HTML-escapes these values by default. User text is now escaped by maketables itself before the `<br>` tags are added, so HTML output is identical across great_tables versions (tested with 0.18, 0.24, and 1.0) and markup in labels or cells is shown as text rather than rendered.
- A comma in `coef_fmt` is now treated as thousands separator when it is part of a valid format spec (e.g. `b:,.2f`), rather than always as a literal delimiter
- Whitespace around fixed-effect names is stripped
- LaTeX compile crash for row-group names containing line breaks

## [0.1.8]

### Added
- **Automated PyPI publishing**: New GitHub Actions workflow publishes to PyPI on tagged releases
- **PEP 561 type marker**: Added `py.typed` for downstream type-checking support
- **Dependabot**: Monthly automated updates for GitHub Actions dependencies
- **Number of clusters stat**: pyfixest extractor now reports number of clusters in model statistics

### Changed
- **Src layout**: Migrated from flat `maketables/` to `src/maketables/` layout
- **Hatchling build backend**: Switched from setuptools to hatchling with hatch-vcs for git-tag-based versioning
- **Python version support**: Dropped EOL Python 3.8/3.9; added 3.13 and 3.14
- **ETable accepts FixestMulti lists**: `ETable` now accepts a list of `FixestMulti` objects in addition to individual models
- **CI improvements**: Pinned Python 3.13 in test matrix; added `frozen: true` to pixi setup

### Fixed
- Deterministic test data with fixed seeds to avoid RNG differences across environments
- pyfixest extractor compatibility with internal API refactors

### Removed
- Stale build artifacts, output files, and dead references cleaned up from the repository

## [0.1.7] - 2025-12-22

### Added
- **Extractor-level default statistics**: Extractors can now specify default statistics via `default_stat_keys()` method
  - `ETable` automatically shows union of defaults when mixing model types
  - User-specified `model_stats` always override extractor defaults
  - Priority: user override > extractor defaults > ETable fallback
- **Custom statistic labels per extractor**: `stat_labels()` method allows model-type-specific labels (e.g., "Pseudo RÂ²" for logit)
- **Plugin extractor system**: `PluginExtractor` allows external packages to add maketables compatibility without explicit support in the library
  - Packages implement methods like `__maketables_coef_table__`, `__maketables_stat__()`, `__maketables_depvar__` on their model classes
  - Enables integration with any model class without modifying maketables source code
  - Use case: Researchers and package maintainers can make their custom models work with maketables
- **Typst output**: Added support for output to Typst
- **Support for Lifelines**: New extractor for survival analysis models from the Lifelines package
- **Enhanced `inspect_model()` function**: Shows which statistics are displayed by default for each model type
- **Snapshot tests**: Snapshot testing for API and model classes (statsmodels, pyfixest, linearmodels)

### Changed
- **Improved extractor protocol documentation**: Enhanced docstrings for `ModelExtractor` with clearer requirements and examples
- **Streamlined documentation**: Updated all example notebooks to reflect new defaults and best practices

### Fixed
- Documentation bugs and typos
- Improved code examples in documentation notebooks


---

[0.1.8]: https://github.com/py-econometrics/maketables/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/py-econometrics/maketables/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/py-econometrics/maketables/releases/tag/v0.1.6
