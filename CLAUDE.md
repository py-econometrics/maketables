# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MakeTables is a Python package for creating publication-ready tables from regression results (pyfixest, statsmodels, linearmodels, lifelines, Stata), descriptive statistics, and balance tables. Outputs to HTML (Great Tables), LaTeX, Word (DOCX), and Typst.

## Development Commands

Uses **Pixi** (conda-based) for environment management. Python 3.13.

```bash
# Run tests
pixi run -e dev tests

# Run a single test file or specific test
pixi run -e dev pytest tests/models/test_pyfixest.py -v
pixi run -e dev pytest tests/api/test_formatting.py::test_name -v

# Update snapshot tests (syrupy)
pixi run -e dev tests-update-snapshots

# Lint and format (ruff via pre-commit)
pixi run -e dev check

# Preview docs (Quarto)
pixi run -e docs docs-preview
```

## Architecture

Source code lives in `src/maketables/` (src layout). Build uses hatchling with hatch-vcs for git-tag-based versioning.

### Class Hierarchy
```
MTable (base - src/maketables/mtable.py)
├── DTable (descriptive stats - src/maketables/dtable.py)
│   └── BTable (balance tables - src/maketables/btable.py)
└── ETable (regression tables - src/maketables/etable.py)
```

- **MTable**: Base class handling all output formats, styling, captions, notes, row grouping
- **ETable**: Extracts coefficients/stats from fitted models using the extractor system
- **DTable**: Computes descriptive statistics with grouping support
- **BTable**: Extends DTable with group difference p-values

### Extractor System (src/maketables/extractors.py)

Plugin architecture using a runtime-checkable `ModelExtractor` Protocol. Each extractor implements `can_handle()`, `coef_table()`, `depvar()`, `stat()`, etc. Built-in extractors for pyfixest, statsmodels, linearmodels. Optional extractors for Stata (`pystata_extractor.py`) and lifelines via conditional imports. New model types are added by implementing the Protocol and calling `register_extractor()`.

### Output Rendering

`make(type='gt'|'tex'|'docx'|'typst')` produces format-specific output. Auto-detects Jupyter vs Quarto for display. `save(path)` exports to file; `update(path)` does in-place DOCX updates.

## Code Style

- **Ruff** for linting and formatting (replaces black/flake8/isort)
- Line length: 88 characters
- Docstrings: numpy convention
- Tests don't require module/function docstrings

## Testing

- **pytest** with **syrupy** snapshot testing
- Test fixtures in `tests/conftest.py` use deterministic seeded data
- Snapshot files live alongside test files in `__snapshots__/` dirs
- After changing output, update snapshots and verify diffs are intentional
