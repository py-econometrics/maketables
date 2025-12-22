# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.7] - 2025-12-22

### Added
- **Extractor-level default statistics**: Extractors can now specify default statistics via `default_stat_keys()` method
  - `ETable` automatically shows union of defaults when mixing model types
  - User-specified `model_stats` always override extractor defaults
  - Priority: user override > extractor defaults > ETable fallback
- **Custom statistic labels per extractor**: `stat_labels()` method allows model-type-specific labels (e.g., "Pseudo R²" for logit)
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

[unreleased]: https://github.com/py-econometrics/maketables/compare/v0.1.7...HEAD
[0.1.7]: https://github.com/py-econometrics/maketables/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/py-econometrics/maketables/releases/tag/v0.1.6
