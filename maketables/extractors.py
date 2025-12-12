"""
Statistical Model Extractor System for MakeTables

This module provides a unified interface for extracting statistical information
from various Python statistical modeling packages (statsmodels, pyfixest, linearmodels).
The extractor system uses a Protocol-based design for type safety and extensibility.
"""

from typing import Any, ClassVar, Protocol, runtime_checkable

import numpy as np
import pandas as pd

from .importdta import get_var_labels

# Optional imports for built-ins
try:
    from pyfixest.estimation.feiv_ import Feiv
    from pyfixest.estimation.feols_ import Feols
    from pyfixest.estimation.fepois_ import Fepois
except Exception:
    Feols = Fepois = Feiv = ()  # type: ignore

try:
    # Import linearmodels result classes (not model classes!)
    from linearmodels.panel.results import PanelResults
    from linearmodels.iv.results import IVResults
    HAS_LINEARMODELS = True
    # All panel results inherit from PanelResults
    # All IV results inherit from IVResults (including AbsorbingLS)
    PanelOLSResults = RandomEffectsResults = PanelResults
    IV2SLSResults = IVGMMResults = IVResults
except Exception:
    HAS_LINEARMODELS = False
    PanelOLSResults = RandomEffectsResults = IV2SLSResults = IVGMMResults = ()  # type: ignore


@runtime_checkable
class ModelExtractor(Protocol):
    """
    Protocol defining the interface for statistical model extractors.

    This protocol ensures that all extractor implementations provide a consistent
    interface for extracting coefficients, statistics, and metadata from statistical models.
    The @runtime_checkable decorator allows isinstance() checks at runtime.
    """

    def can_handle(self, model: Any) -> bool:
        """Check if this extractor can handle the given model type."""
        ...

        def coef_table(self, model: Any) -> pd.DataFrame:
                """
                Extract a standardized coefficient table.

                General principle
                - Any column returned by this DataFrame can be referenced as a token
                    in ETable's coef_fmt string.
                - Reserved shorthand tokens (and canonical column names) are:
                    "b" → point estimate, "se" → standard error, "t" → t statistic,
                    "p" → p-value. These columns must exist in the returned DataFrame.

                Requirements
                - Must include at least columns: "b", "se", "p".
                - May include optional columns like "t", "ci95l", "ci95u", "ci90l", "ci90u",
                    or any other model-specific metrics.

                Returns
                -------
                        DataFrame indexed by coefficient names with the columns described above.
                """
        ...

    def depvar(self, model: Any) -> str:
        """Extract the dependent variable name from the model."""
        ...

    def fixef_string(self, model: Any) -> str | None:
        """
        Extract fixed effects specification as a string.

        Returns
        -------
            String describing fixed effects (e.g., "entity+time") or None if no fixed effects.
        """
        ...

    def stat(self, model: Any, key: str) -> Any:
        """
        Extract a specific statistic from the model.

        Args:
            model: Statistical model object
            key: Statistic key (e.g., "N", "r2", "adj_r2", "fvalue")

        Returns
        -------
            The requested statistic value or None if not available.
        """
        ...

    def vcov_info(self, model: Any) -> dict[str, Any]:
        """
        Extract variance-covariance matrix information.

        Returns
        -------
            Dictionary with vcov_type and clustervar information.
        """
        ...

    def var_labels(self, model: Any) -> dict[str, str] | None:
        """
        Extract variable labels from the model's data. Note: this allows to access maketables'
        variable labeling system if the model retains a reference to the original DataFrame and
        checks whether the DataFrame has variable labels (attribute `var_labels`).

        Returns
        -------
            Dictionary mapping variable names to descriptive labels, or None if unavailable.
        """
        ...

    def supported_stats(self, model: Any) -> set[str]:
        """
        Get the set of statistics this extractor can provide for the given model.

        Returns
        -------
            Set of statistic keys that are available for this model.
        """
        ...


_EXTRACTOR_REGISTRY: list[ModelExtractor] = []


def register_extractor(extractor: ModelExtractor) -> None:
    """
    Register a model extractor in the global registry.

    Args:
        extractor: ModelExtractor instance to register.
    """
    _EXTRACTOR_REGISTRY.append(extractor)


def clear_extractors() -> None:
    """Clear all registered extractors from the registry."""
    _EXTRACTOR_REGISTRY.clear()


class PluginExtractor:
    """
    Generic extractor for models implementing the maketables plug-in format.
    
    Packages can make their model classes compatible with maketables by implementing
    any combination of the following attributes/methods on their model result class:
    
    - __maketables_coef_table__ (property): Returns pd.DataFrame with columns: b, se, t, p, etc.
    - __maketables_stat__(key) (method): Returns statistic by key (e.g., 'N', 'r2', 'adj_r2')
    - __maketables_depvar__ (property): Returns dependent variable name as str
    - __maketables_fixef_string__ (property): Returns fixed effects string or None
    - __maketables_var_labels__ (property): Returns dict mapping var names to labels or None
    - __maketables_vcov_info__ (property): Returns dict with vcov metadata or None
    
    See PLUGIN_EXTRACTOR_FORMAT.md for detailed specifications.
    """
    
    def can_handle(self, model: Any) -> bool:
        """Check if model implements the plug-in interface (has coef_table attribute)."""
        return hasattr(model, "__maketables_coef_table__")
    
    def coef_table(self, model: Any) -> pd.DataFrame:
        """Extract coefficient table from plugin attribute."""
        coef_df = model.__maketables_coef_table__
        if isinstance(coef_df, pd.DataFrame):
            if coef_df.index.name != "Coefficient":
                coef_df = coef_df.copy()
                coef_df.index.name = "Coefficient"
            return coef_df
        raise ValueError(
            f"__maketables_coef_table__ must return a pd.DataFrame, got {type(coef_df)}"
        )
    
    def depvar(self, model: Any) -> str:
        """Extract dependent variable name from plugin attribute."""
        if hasattr(model, "__maketables_depvar__"):
            return model.__maketables_depvar__
        return "Dependent Variable"
    
    def fixef_string(self, model: Any) -> str | None:
        """Extract fixed effects string from plugin attribute."""
        if hasattr(model, "__maketables_fixef_string__"):
            return model.__maketables_fixef_string__
        return None
    
    def stat(self, model: Any, key: str) -> Any:
        """Extract a statistic using the plugin method."""
        if hasattr(model, "__maketables_stat__"):
            return model.__maketables_stat__(key)
        return None
    
    def vcov_info(self, model: Any) -> dict[str, Any]:
        """Extract variance-covariance information from plugin attribute."""
        if hasattr(model, "__maketables_vcov_info__"):
            info = model.__maketables_vcov_info__
            return info if isinstance(info, dict) else {}
        return {}
    
    def var_labels(self, model: Any) -> dict[str, str] | None:
        """Extract variable labels from plugin attribute."""
        if hasattr(model, "__maketables_var_labels__"):
            return model.__maketables_var_labels__
        return None
    
    def supported_stats(self, model: Any) -> set[str]:
        """Return set of statistics that can be extracted via __maketables_stat__."""
        # Try to discover supported stats by checking if __maketables_stat__ exists
        if hasattr(model, "__maketables_stat__"):
            # Can't easily determine what's supported without calling it,
            # so return an empty set. Extractors can call stat() and it will
            # return None if not available.
            return set()
        return set()


def get_extractor(model: Any) -> ModelExtractor:
    """
    Find and return the appropriate extractor for a given model.

    Strategy (in order):
    1. Check registered extractors (package-specific implementations)
    2. Check for plug-in format (__maketables_coef_table__ attribute)
    
    The plug-in format allows external packages to integrate without modifying maketables.
    See PLUGIN_EXTRACTOR_FORMAT.md for specifications.

    Args:
        model: Statistical model object to find an extractor for.

    Returns
    -------
        ModelExtractor instance that can handle the model.

    Raises
    ------
        TypeError: If no registered extractor or plug-in format can handle the model type.
    """
    for ex in _EXTRACTOR_REGISTRY:
        try:
            if ex.can_handle(model):
                return ex
        except Exception:
            continue
    
    # Check for plug-in format as fallback
    plugin_extractor = PluginExtractor()
    try:
        if plugin_extractor.can_handle(model):
            return plugin_extractor
    except Exception:
        pass
    
    # Build helpful error message
    model_type = type(model).__name__
    model_module = type(model).__module__
    
    error_msg = (
        f"No extractor available for model type: {model_type} from {model_module}\n\n"
        f"Registered extractors ({len(_EXTRACTOR_REGISTRY)}):\n"
    )
    
    for i, extractor in enumerate(_EXTRACTOR_REGISTRY, 1):
        extractor_name = type(extractor).__name__
        error_msg += f"  {i}. {extractor_name}\n"
    
    error_msg += (
        "\nAlternatively, implement the plug-in extractor format by adding these attributes "
        "to your model class:\n"
        "  - __maketables_coef_table__ (property): Returns DataFrame with columns b, se, t, p\n"
        "  - __maketables_stat__(key) (method): Returns statistic by key\n"
        "  - __maketables_depvar__ (property): Returns dependent variable name\n\n"
        "See PLUGIN_EXTRACTOR_FORMAT.md for full specifications.\n\n"
        "To register a custom extractor, implement the ModelExtractor protocol "
        "and use register_extractor()."
    )
    
    raise TypeError(error_msg)


def inspect_model(model: Any, long: bool = False) -> None:
    """
    Inspect a fitted model by printing its extracted coefficient table columns and available statistics.
    
    By default, shows a concise summary. Use long=True for detailed output with sample values.
    
    Parameters
    ----------
    model : Any
        A fitted statistical model (from statsmodels, pyfixest, linearmodels, lifelines, etc.)
    long : bool, optional
        If True, show detailed output with sample values and first few rows. Default is False.
    
    Examples
    --------
    >>> from lifelines import CoxPHFitter
    >>> from lifelines.datasets import load_rossi
    >>> cph = CoxPHFitter().fit(load_rossi(), 'week', 'arrest')
    >>> inspect_model(cph)  # Concise summary
    >>> inspect_model(cph, long=True)  # Detailed output
    """
    try:
        extractor = get_extractor(model)
    except TypeError as e:
        print(f"Error: {e}")
        return
    
    print(f"\n{'='*60}")
    print(f"Model: {type(model).__name__} | Extractor: {type(extractor).__name__}")
    print(f"{'='*60}\n")
    
    # Extract and display coefficient table structure
    print("COEFFICIENT TABLE COLUMNS:")
    try:
        coef_df = extractor.coef_table(model)
        
        if long:
            # Detailed output with sample values
            print("-" * 60)
            print(f"Index name: {coef_df.index.name}")
            print(f"Number of coefficients: {len(coef_df)}")
            print("\nAvailable columns (non-empty):")
            for col in coef_df.columns:
                non_null = coef_df[col].notna().sum()
                if non_null > 0:
                    sample_val = coef_df[col].dropna().iloc[0] if non_null > 0 else "N/A"
                    print(f"  - {col:15s} ({non_null}/{len(coef_df)} non-null) example: {sample_val}")
            
            print("\nFirst few rows:")
            print(coef_df.head().to_string())
        else:
            # Concise output - just list non-empty columns
            non_empty_cols = [col for col in coef_df.columns if coef_df[col].notna().sum() > 0]
            print(f"  {', '.join(non_empty_cols)}")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    # Extract and display available statistics
    print(f"\nAVAILABLE STATISTICS:")
    try:
        # Try common stats and collect non-None values
        common_stats = [
            "N", "events", "ll", "aic", "bic", "concordance",
            "r2", "adj_r2", "r2_within", "pseudo_r2",
            "fvalue", "f_pvalue", "rmse",
            "llr", "llr_df", "llr_p", "llr_log2p",
            "se_type", "df_model", "df_resid"
        ]
        
        available_stats = []
        stat_values = {}
        for stat_key in common_stats:
            try:
                val = extractor.stat(model, stat_key)
                if val is not None:
                    available_stats.append(stat_key)
                    stat_values[stat_key] = val
            except Exception:
                pass
        
        if long:
            # Detailed output with values
            print("-" * 60)
            supported = extractor.supported_stats(model)
            if supported:
                print(f"Supported stats ({len(supported)}): {', '.join(sorted(supported))}")
            
            print("\nExtracted values (non-empty):")
            if available_stats:
                for stat_key in available_stats:
                    print(f"  {stat_key:15s} = {stat_values[stat_key]}")
            else:
                print("  (no statistics extracted)")
        else:
            # Concise output - just list available stats
            if available_stats:
                print(f"  {', '.join(available_stats)}")
            else:
                print("  (none)")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    # Display other metadata
    print(f"\nOTHER METADATA:")
    try:
        depvar = extractor.depvar(model)
        vcov = extractor.vcov_info(model)
        fixef = extractor.fixef_string(model)
        
        if long:
            # Detailed output
            print("-" * 60)
            print(f"Dependent variable: {depvar}")
            if vcov:
                vcov_type = vcov.get("vcov_type")
                clustervar = vcov.get("clustervar")
                print(f"Variance-covariance type: {vcov_type}")
                if clustervar:
                    print(f"Cluster variable: {clustervar}")
            print(f"Fixed effects: {fixef if fixef else 'None'}")
        else:
            # Concise output
            parts = [f"depvar={depvar}"]
            if vcov and vcov.get("vcov_type"):
                vcov_str = vcov.get("vcov_type")
                if vcov.get("clustervar"):
                    vcov_str += f"({vcov.get('clustervar')})"
                parts.append(f"vcov={vcov_str}")
            if fixef:
                parts.append(f"fixef={fixef}")
            print(f"  {', '.join(parts)}")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    print(f"{'='*60}\n")


# ---------- small helpers ----------


def _follow(obj: Any, chain: list[str]) -> Any:
    """
    Follow a chain of attribute names to extract nested values.

    Args:
        obj: Starting object to traverse from.
        chain: List of attribute names to follow sequentially.

    Returns
    -------
        The final nested attribute value, or None if any attribute in the chain doesn't exist.

    Example:
        _follow(model, ["model", "endog", "name"]) returns model.model.endog.name
    """
    cur = obj
    for a in chain:
        if hasattr(cur, a):
            cur = getattr(cur, a)
        else:
            return None
    return cur


def _get_attr(model: Any, spec: Any) -> Any:
    """
    Resolve a STAT_MAP specification against a model object.

    This function provides a unified way to extract attributes from statistical models
    using different specification formats:

    Args:
        model: Statistical model object to extract from.
        spec: Specification for how to extract the value, can be:
            - str: Direct attribute name ("attr") -> tries model.attr, then model.model.attr
            - tuple/list: Nested attribute path ("a","b","c") -> model.a.b.c via _follow()
            - callable: Function to compute value -> spec(model)

    Returns
    -------
        The extracted value, or None if the specification cannot be resolved.

    Examples
    --------
        _get_attr(model, "nobs")  # Returns model.nobs or model.model.nobs
        _get_attr(model, ("model", "endog", "name"))  # Returns model.model.endog.name
        _get_attr(model, lambda m: m.s2 ** 0.5)  # Returns computed RMSE
    """
    if isinstance(spec, str):
        return getattr(model, spec, getattr(getattr(model, "model", None), spec, None))
    if isinstance(spec, (list, tuple)):
        return _follow(model, list(spec))
    if callable(spec):
        try:
            return spec(model)
        except Exception:
            return None
    return None


# ---------- Built-in extractors ----------


class PyFixestExtractor:
    """
    Extractor for pyfixest models (Feols, Fepois, Feiv).

    Handles models from the pyfixest package, providing access to
    coefficients, statistics, and metadata. Supports clustered standard errors
    and fixed effects specifications.
    """

    def can_handle(self, model: Any) -> bool:
        """Check if model is a pyfixest model type."""
        # If pyfixest types are empty tuples, it means pyfixest is not available
        if Feols == ():
            return False
        try:
            return isinstance(model, (Feols, Fepois, Feiv))
        except Exception:
            return False

    def coef_table(self, model: Any) -> pd.DataFrame:
        """
        Extract coefficient table from pyfixest model using tidy() method.

        Standardizes column names to canonical tokens: b, se, p, t.
        """
        df = model.tidy()
        required = {"Estimate", "Std. Error", "Pr(>|t|)"}
        missing = required - set(df.columns)
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(
                f"PyFixestExtractor: tidy() must contain {missing_list}."
            )

        # Rename to canonical token columns
        rename_map = {
            "Estimate": "b",
            "Std. Error": "se",
            "Pr(>|t|)": "p",
            "t value": "t",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        # Rename confidence interval columns if present
        if "2.5%" in df.columns and "97.5%" in df.columns:
            df = df.rename(columns={"2.5%": "ci95l", "97.5%": "ci95u"})

        # Reorder canonical columns first when present
        col_order = [c for c in ["b", "se", "t", "p"] if c in df.columns]
        remaining = [c for c in df.columns if c not in col_order]
        df = df[col_order + remaining]

        return df

    def depvar(self, model: Any) -> str:
        """Extract dependent variable name from pyfixest model."""
        return getattr(model, "_depvar", "y")

    def fixef_string(self, model: Any) -> str | None:
        """Extract fixed effects specification string from pyfixest model."""
        return getattr(model, "_fixef", None)

    # Build a clean map of unified stat keys -> pyfixest attributes/callables
    STAT_MAP: ClassVar[dict[str, Any]] = {
        "N": "_N",
        "se_type": lambda m: (
            "by: " + "+".join(getattr(m, "_clustervar", []))
            if getattr(m, "_vcov_type", None) == "CRV"
            and getattr(m, "_clustervar", None)
            else getattr(m, "_vcov_type", None)
        ),
        "r2": "_r2",
        "adj_r2": "_r2_adj",
        "r2_within": "_r2_within",
        "adj_r2_within": "_adj_r2_within",
        "rmse": "_rmse",
        "fvalue": "_F_stat",
        "f_statistic": "_f_stat_1st_stage",
        # pyfixest may return a sequence; take the first element
        "deviance": lambda m: (
            (getattr(m, "deviance", None)[0])
            if isinstance(
                getattr(m, "deviance", None), (list, tuple, np.ndarray, pd.Series)
            )
            else getattr(m, "deviance", None)
        ),
    }

    def stat(self, model: Any, key: str) -> Any:
        """
        Extract a statistic from the pyfixest model using STAT_MAP.

        Args:
            model: Pyfixest model object.
            key: Statistic key (e.g., "N", "r2", "se_type").

        Returns
        -------
            The requested statistic value, with special handling for sample size (N).
        """
        spec = self.STAT_MAP.get(key)
        if spec is None:
            return None
        val = _get_attr(model, spec)
        if key == "N" and val is not None:
            try:
                return int(val)
            except Exception:
                return val
        return val

    def vcov_info(self, model: Any) -> dict[str, Any]:
        """Extract variance-covariance matrix type and clustering information."""
        return {
            "vcov_type": getattr(model, "_vcov_type", None),
            "clustervar": getattr(model, "_clustervar", None),
        }

    def var_labels(self, model: Any) -> dict[str, str] | None:
        """Extract variable labels from the model's data DataFrame when available."""
        df = getattr(model, "_data", None)
        if isinstance(df, pd.DataFrame):
            try:
                return get_var_labels(df, include_defaults=True)
            except Exception:
                return None
        return None

    def supported_stats(self, model: Any) -> set[str]:
        """Return set of statistics available for the given pyfixest model."""
        return {
            k for k, spec in self.STAT_MAP.items() if _get_attr(model, spec) is not None
        }


class StatsmodelsExtractor:
    """
    Extractor for statsmodels regression results.

    Handles most statsmodels result objects that have the standard interface
    with params, bse (standard errors), and pvalues attributes. Supports
    various regression types including OLS, GLM, and others.
    """

    def can_handle(self, model: Any) -> bool:
        """Check if model has the standard statsmodels result interface."""
        return all(hasattr(model, a) for a in ("params", "bse", "pvalues"))

    def coef_table(self, model: Any) -> pd.DataFrame:
        """Extract coefficient table from statsmodels result with canonical tokens."""
        params = pd.Series(model.params)
        params.index.name = "Coefficient"
        se = pd.Series(getattr(model, "bse", np.nan), index=params.index)
        pvalues = pd.Series(getattr(model, "pvalues", np.nan), index=params.index)
        tvalues = getattr(model, "tvalues", None)

        df = pd.DataFrame(
            {
                "b": pd.to_numeric(params, errors="coerce"),
                "se": pd.to_numeric(se, errors="coerce"),
                "p": pd.to_numeric(pvalues, errors="coerce"),
            },
            index=params.index,
        )

        if tvalues is not None:
            df["t"] = pd.to_numeric(
                pd.Series(tvalues, index=params.index), errors="coerce"
            )

        # Extract confidence intervals if available
        if hasattr(model, "conf_int"):
            try:
                ci = model.conf_int(alpha=0.05)  # 95% CI
                df["ci95l"] = pd.to_numeric(ci.iloc[:, 0], errors="coerce")
                df["ci95u"] = pd.to_numeric(ci.iloc[:, 1], errors="coerce")
            except Exception:
                df["ci95l"] = df["b"] - 1.96 * df["se"]
                df["ci95u"] = df["b"] + 1.96 * df["se"]
        else:
            df["ci95l"] = df["b"] - 1.96 * df["se"]
            df["ci95u"] = df["b"] + 1.96 * df["se"]

        # Also add 90% CI
        if hasattr(model, "conf_int"):
            try:
                ci90 = model.conf_int(alpha=0.10)  # 90% CI
                df["ci90l"] = pd.to_numeric(ci90.iloc[:, 0], errors="coerce")
                df["ci90u"] = pd.to_numeric(ci90.iloc[:, 1], errors="coerce")
            except Exception:
                df["ci90l"] = df["b"] - 1.645 * df["se"]
                df["ci90u"] = df["b"] + 1.645 * df["se"]
        else:
            df["ci90l"] = df["b"] - 1.645 * df["se"]
            df["ci90u"] = df["b"] + 1.645 * df["se"]

        # Reorder columns
        ordered = [c for c in ["b", "se", "t", "p", "ci95l", "ci95u", "ci90l", "ci90u"] if c in df.columns]
        df = df[ordered]

        return df

    def depvar(self, model: Any) -> str:
        """
        Extract dependent variable name from statsmodels result.

        Tries multiple common locations for the dependent variable name
        in statsmodels results objects.

        Returns
        -------
            Dependent variable name or "y" if not found.
        """
        for chain in [
            ("model", "endog_names"),
            ("endog_names",),
            ("model", "endog", "name"),
        ]:
            obj = model
            ok = True
            for a in chain:
                if hasattr(obj, a):
                    obj = getattr(obj, a)
                else:
                    ok = False
                    break
            if ok and isinstance(obj, str):
                return obj
        return "y"

    def fixef_string(self, model: Any) -> str | None:
        """Statsmodels doesn't typically have fixed effects notation."""
        return None

    # Unified stat keys -> statsmodels attributes/callables
    STAT_MAP: ClassVar[dict[str, Any]] = {
        "N": "nobs",
        "se_type": "cov_type",
        "r2": "rsquared",
        "adj_r2": "rsquared_adj",
        "pseudo_r2": "prsquared",
        "ll": "llf",
        "llnull": "llnull",
        "aic": "aic",
        "bic": "bic",
        "df_model": "df_model",
        "df_resid": "df_resid",
        "deviance": "deviance",
        "null_deviance": "null_deviance",
        "fvalue": "fvalue",
        "f_pvalue": "f_pvalue",
    }

    def stat(self, model: Any, key: str) -> Any:
        """Extract a specific statistic from a statsmodels fitted model."""
        spec = self.STAT_MAP.get(key)
        if spec is None:
            return None
        val = _get_attr(model, spec)
        if key == "N" and val is not None:
            try:
                return int(val)
            except Exception:
                return val
        return val

    def vcov_info(self, model: Any) -> dict[str, Any]:
        """Extract variance-covariance information from a statsmodels fitted model."""
        return {"vcov_type": getattr(model, "cov_type", None), "clustervar": None}

    def var_labels(self, model: Any) -> dict[str, str] | None:
        """Extract variable labels from a statsmodels fitted model."""
        # Try common statsmodels formula-api locations for the original DataFrame
        candidates = [
            ("model", "model", "data", "frame"),
            ("model", "data", "frame"),
        ]
        for chain in candidates:
            df = _follow(model, list(chain))
            if isinstance(df, pd.DataFrame):
                try:
                    return get_var_labels(df, include_defaults=True)
                except Exception:
                    return None
        return None

    def supported_stats(self, model: Any) -> set[str]:
        """Return set of statistics available for the given statsmodels model."""
        return {
            k for k, spec in self.STAT_MAP.items() if _get_attr(model, spec) is not None
        }


class LinearmodelsExtractor:
    """Extractor for linearmodels regression results."""

    def can_handle(self, model: Any) -> bool:
        """Check if this extractor can handle the given model."""
        # If linearmodels types are empty tuples, linearmodels is not available
        if PanelOLSResults == ():
            return False
        
        # Check module first (fast check)
        mod = type(model).__module__ or ""
        if not mod.startswith("linearmodels."):
            return False
        
        # Check if it's a linearmodels result type
        # Need to handle both PanelResults and IVResults (AbsorbingLS is IVResults)
        if isinstance(model, (PanelOLSResults, IV2SLSResults)):
            return True
        
        # Fallback: check for required attributes
        return (
            hasattr(model, "params")
            and hasattr(model, "pvalues")
            and (hasattr(model, "std_errors") or hasattr(model, "std_error"))
        )

    def coef_table(self, model: Any) -> pd.DataFrame:
        """Extract coefficient table from a linearmodels fitted model with token columns."""
        params = pd.Series(model.params)
        
        # Handle both std_errors (panel) and std_error (IV/AbsorbingLS)
        se_attr = "std_errors" if hasattr(model, "std_errors") else "std_error"
        se = pd.Series(getattr(model, se_attr, np.nan), index=params.index)
        pvalues = pd.Series(getattr(model, "pvalues", np.nan), index=params.index)
        tstats = getattr(model, "tstats", None)

        df = pd.DataFrame(
            {
                "b": pd.to_numeric(params, errors="coerce"),
                "se": pd.to_numeric(se, errors="coerce"),
                "p": pd.to_numeric(pvalues, errors="coerce"),
            },
            index=params.index,
        )
        
        if tstats is not None:
            df["t"] = pd.to_numeric(
                pd.Series(tstats, index=params.index), errors="coerce"
            )
        
        # Extract confidence intervals if available
        if hasattr(model, "conf_int"):
            try:
                ci95 = model.conf_int(level=0.95)
                df["ci95l"] = pd.to_numeric(ci95.iloc[:, 0], errors="coerce")
                df["ci95u"] = pd.to_numeric(ci95.iloc[:, 1], errors="coerce")
            except Exception:
                df["ci95l"] = df["b"] - 1.96 * df["se"]
                df["ci95u"] = df["b"] + 1.96 * df["se"]
        else:
            df["ci95l"] = df["b"] - 1.96 * df["se"]
            df["ci95u"] = df["b"] + 1.96 * df["se"]
        
        # Also add 90% CI
        if hasattr(model, "conf_int"):
            try:
                ci90 = model.conf_int(level=0.90)
                df["ci90l"] = pd.to_numeric(ci90.iloc[:, 0], errors="coerce")
                df["ci90u"] = pd.to_numeric(ci90.iloc[:, 1], errors="coerce")
            except Exception:
                df["ci90l"] = df["b"] - 1.645 * df["se"]
                df["ci90u"] = df["b"] + 1.645 * df["se"]
        else:
            df["ci90l"] = df["b"] - 1.645 * df["se"]
            df["ci90u"] = df["b"] + 1.645 * df["se"]
        
        ordered = [c for c in ["b", "se", "t", "p", "ci95l", "ci95u", "ci90l", "ci90u"] if c in df.columns]
        df = df[ordered]
        
        return df

    def depvar(self, model: Any) -> str:
        """Extract dependent variable name from a linearmodels fitted model."""
        # Try common locations
        for chain in [
            ("model", "formula"),  # 'y ~ x1 + x2'
            ("model", "dependent", "name"),
            ("model", "dependent", "var_name"),
            ("model", "dependent", "pandas", "name"),
            ("model", "dependent", "vars", 0),  # AbsorbingLS stores vars as list
        ]:
            val = _follow(model, list(chain))
            if isinstance(val, str):
                if chain[-1] == "formula" and "~" in val:
                    return val.split("~", 1)[0].strip()
                return val
        
        # For AbsorbingLS, try to get column name from dependent DataFrame
        mdl = getattr(model, "model", None)
        if mdl is not None:
            dep = getattr(mdl, "dependent", None)
            if dep is not None:
                if hasattr(dep, "cols"):
                    # dep.cols contains the column names
                    cols = dep.cols
                    if isinstance(cols, list) and len(cols) > 0:
                        return cols[0]
                elif hasattr(dep, "dataframe") and hasattr(dep.dataframe, "columns"):
                    return dep.dataframe.columns[0]
        
        return "y"

    def fixef_string(self, model: Any) -> str | None:
        """
        Extract fixed effects string from a linearmodels fitted model.
        
        For PanelOLS: Returns actual index names (e.g., "nr+year")
        For AbsorbingLS: Returns absorbed variable names (e.g., "firm_id+year")
        """
        mdl = getattr(model, "model", None)
        if mdl is None:
            return None
        
        # Check if this is an AbsorbingLS model
        model_type = type(mdl).__name__
        if model_type == "AbsorbingLS":
            # For AbsorbingLS, the absorb parameter is stored as _absorb
            absorb_data = getattr(mdl, "_absorb", None)
            if absorb_data is not None:
                # absorb_data is the DataFrame that was passed as absorb parameter
                if hasattr(absorb_data, "columns"):
                    return "+".join(absorb_data.columns.tolist())
                # Fallback: if it's a Categorical object with pandas attribute
                if hasattr(absorb_data, "pandas") and hasattr(absorb_data.pandas, "columns"):
                    return "+".join(absorb_data.pandas.columns.tolist())
            return None
        
        # For PanelOLS/RandomEffects models
        has_entity = getattr(mdl, "entity_effects", False)
        has_time = getattr(mdl, "time_effects", False)
        has_other = getattr(mdl, "other_effects", None)
        
        if not (has_entity or has_time or has_other):
            return None
        
        # Try to extract actual variable names from panel structure
        entity_name = "entity"
        time_name = "time"
        
        dependent = getattr(mdl, "dependent", None)
        if dependent is not None and hasattr(dependent, "dataframe"):
            idx = dependent.dataframe.index
            if hasattr(idx, "names") and len(idx.names) >= 2:
                entity_name = idx.names[0] or "entity"
                time_name = idx.names[1] or "time"
        
        # Build fixed effects string
        parts = []
        if has_entity:
            parts.append(entity_name)
        if has_time:
            parts.append(time_name)
        if has_other:
            parts.append("other")
        
        return "+".join(parts) if parts else None

    # Unified stat keys -> linearmodels attributes/callables
    STAT_MAP: ClassVar[dict[str, Any]] = {
        # Sizes / DoF
        "N": "nobs",
        "df_model": "df_model",
        "df_resid": "df_resid",
        # VCOV type
        "se_type": "cov_type",
        # R-squared family
        "r2": "rsquared",
        "adj_r2": "rsquared_adj",
        "r2_within": "rsquared_within",
        "r2_between": "rsquared_between",
        "r2_overall": "rsquared_overall",
        # Information criteria / likelihood (if exposed)
        "aic": "aic",
        "bic": "bic",
        "ll": "loglik",
        # F-stat (when available)
        "fvalue": lambda m: getattr(getattr(m, "f_statistic", None), "stat", None),
        "f_pvalue": lambda m: getattr(getattr(m, "f_statistic", None), "pval", None),
        # Error scale / RMSE
        "rmse": lambda m: (
            getattr(m, "root_mean_squared_error", None)
            if hasattr(m, "root_mean_squared_error")
            else (float(m.s2) ** 0.5 if hasattr(m, "s2") and m.s2 is not None else None)
        ),
        # IV diagnostics: TODO
       
    }

    def stat(self, model: Any, key: str) -> Any:
        """Extract a specific statistic from a linearmodels fitted model."""
        spec = self.STAT_MAP.get(key)
        if spec is None:
            return None
        val = _get_attr(model, spec)
        if key == "N" and val is not None:
            try:
                return int(val)
            except Exception:
                return val
        return val

    def vcov_info(self, model: Any) -> dict[str, Any]:
        """Extract variance-covariance information from a linearmodels fitted model."""
        return {"vcov_type": getattr(model, "cov_type", None), "clustervar": None}

    def var_labels(self, model: Any) -> dict[str, str] | None:
        """Extract variable labels from a linearmodels fitted model."""
        # Try to locate original DataFrame
        candidates = [
            ("model", "data", "frame"),
            ("model", "dataframe"),
        ]
        for chain in candidates:
            df = _follow(model, list(chain))
            if isinstance(df, pd.DataFrame):
                try:
                    return get_var_labels(df, include_defaults=True)
                except Exception:
                    return None
        return None

    def supported_stats(self, model: Any) -> set[str]:
        """Return set of statistics available for the given linearmodels model."""
        return {
            k for k, spec in self.STAT_MAP.items() if _get_attr(model, spec) is not None
        }

# Register built-ins
clear_extractors()
register_extractor(PyFixestExtractor())
register_extractor(LinearmodelsExtractor())
register_extractor(StatsmodelsExtractor())


class LifelinesExtractor:
    """Extractor for lifelines survival regression fitters (CoxPH, AFT)."""

    def can_handle(self, model: Any) -> bool:
        """Check if object looks like a lifelines fitted model."""
        mod = type(model).__module__ or ""
        if not mod.startswith("lifelines."):
            return False
        # lifelines fitters expose a `summary` DataFrame after fitting
        return hasattr(model, "summary") and isinstance(getattr(model, "summary", None), pd.DataFrame)

    def coef_table(self, model: Any) -> pd.DataFrame:
        """
        Extract coefficient table from lifelines fitter.

        Maps columns to maketables tokens :
        - b, se, t (z), p, ci95l, ci95u
        - hr (hazard ratio = exp(coef)) and hr_ci95l/hr_ci95u when present
        """
        df = model.summary.copy()

        # Determine coefficient name index
        if df.index.name != "Coefficient":
            df.index.name = "Coefficient"

        # lifelines column variants across fitters
        # Note: p and z already named adequately in lifelines summary
        rename_map = {}
        cols = set(df.columns)

        if "coef" in cols:
            rename_map["coef"] = "b"

        if "se(coef)" in cols:
            rename_map["se(coef)"] = "se"
    
        if "coef lower 95%" in cols:
            rename_map["coef lower 95%"] = "ci95l"
        
        if "coef upper 95%" in cols:
            rename_map["coef upper 95%"] = "ci95u"

        # 95% CI
        lower95 = None
        upper95 = None
        for lcol in ["coef lower 95%", "lower 95%"]:
            if lcol in cols:
                lower95 = lcol
                break
        for ucol in ["coef upper 95%", "upper 95%"]:
            if ucol in cols:
                upper95 = ucol
                break

        if lower95 and upper95:
            rename_map[lower95] = "ci95l"
            rename_map[upper95] = "ci95u"

        # Hazard ratios and their CI when present
        if "exp(coef)" in cols:
            rename_map["exp(coef)"] = "hr"
        
        hr_l95 = None
        hr_u95 = None
        for lcol in ["exp(coef) lower 95%"]:
            if lcol in cols:
                hr_l95 = lcol
                break
        for ucol in ["exp(coef) upper 95%"]:
            if ucol in cols:
                hr_u95 = ucol
                break
        if hr_l95:
            rename_map[hr_l95] = "hr_ci95l"
        if hr_u95:
            rename_map[hr_u95] = "hr_ci95u"

        df = df.rename(columns=rename_map)

        # Ensure required columns exist (only from summary)
        required = {"b", "se", "p"}
        missing = required - set(df.columns)
        if missing:
            missing_list = ", ".join(sorted(missing))
            raise ValueError(f"LifelinesExtractor: summary missing required columns: {missing_list}.")


        # Reorder canonical columns first (include hazard ratio tokens when present)
        ordered = [c for c in ["b", "se", "z", "p", "ci95l", "ci95u", "hr", "hr_ci95l", "hr_ci95u"] if c in df.columns]
        df = df[ordered + [c for c in df.columns if c not in ordered]]
        return df

    def depvar(self, model: Any) -> str:
        """Return event_col."""
        return getattr(model, "event_col", None) or getattr(model, "event_col_", None) or "duration"

    def fixef_string(self, model: Any) -> str | None:
        """Survival models typically have no fixed effects string."""
        return None

    STAT_MAP: ClassVar[dict[str, Any]] = {
        # Basic counts
        "N": lambda m: (
            getattr(m, "_n_examples", None) or 
            (getattr(m, "weights", None).sum() if hasattr(m, "weights") and getattr(m, "weights", None) is not None else None)
        ),
        "events": lambda m: (
            getattr(m, "weights", None)[getattr(m, "event_observed", None) > 0].sum()
            if hasattr(m, "weights") and hasattr(m, "event_observed") 
            and getattr(m, "weights", None) is not None 
            and getattr(m, "event_observed", None) is not None
            else None
        ),
        # Likelihood
        "ll": lambda m: getattr(m, "log_likelihood_", None),
        # Model fit measures
        "aic": lambda m: (
            getattr(m, "AIC_partial_", None)
            if hasattr(m, "AIC_partial_") else getattr(m, "AIC_", None)
        ),
        "concordance": lambda m: getattr(m, "concordance_index_", None) or getattr(m, "concordance_index", None),
        # Log-likelihood ratio test - call the method if it exists
        "llr": lambda m: (
            getattr(m.log_likelihood_ratio_test(), "test_statistic", None)
            if hasattr(m, "log_likelihood_ratio_test") and callable(m.log_likelihood_ratio_test)
            else None
        ),
        "llr_df": lambda m: (
            getattr(m.log_likelihood_ratio_test(), "degrees_freedom", None)
            if hasattr(m, "log_likelihood_ratio_test") and callable(m.log_likelihood_ratio_test)
            else None
        ),
        "llr_p": lambda m: (
            getattr(m.log_likelihood_ratio_test(), "p_value", None)
            if hasattr(m, "log_likelihood_ratio_test") and callable(m.log_likelihood_ratio_test)
            else None
        ),
        "llr_log2p": lambda m: (
            (-(np.log2(p)))
            if hasattr(m, "log_likelihood_ratio_test") and callable(m.log_likelihood_ratio_test)
            and (p := getattr(m.log_likelihood_ratio_test(), "p_value", None)) is not None and p > 0
            else None
        ),
    }

    def stat(self, model: Any, key: str) -> Any:
        spec = self.STAT_MAP.get(key)
        if spec is None:
            return None
        val = _get_attr(model, spec)
        if key == "N" and val is not None:
            try:
                return int(val)
            except Exception:
                return val
        return val

    def vcov_info(self, model: Any) -> dict[str, Any]:
        """
        Extract variance-covariance information from lifelines models.
        
        Detects:
        - robust: whether robust (sandwich) standard errors were requested
        - cluster_col: column name used for clustering
        """
        robust = getattr(model, "robust", False)
        cluster_col = getattr(model, "cluster_col", None)
        
        # Determine vcov_type based on robust and cluster_col
        if cluster_col:
            vcov_type = "cluster"
        elif robust:
            vcov_type = "robust"
        else:
            vcov_type = None
        
        return {
            "vcov_type": vcov_type,
            "clustervar": cluster_col
        }

    def var_labels(self, model: Any) -> dict[str, str] | None:
        # Try to find original DataFrame from cached fit args
        df = None
        try:
            args = getattr(model, "_cached_fit_arguments", {})
            df = args.get("df", None)
        except Exception:
            df = None
        if isinstance(df, pd.DataFrame):
            try:
                return get_var_labels(df, include_defaults=True)
            except Exception:
                return None
        return None

    def supported_stats(self, model: Any) -> set[str]:
        return {k for k, spec in self.STAT_MAP.items() if _get_attr(model, spec) is not None}


# Register lifelines extractor
register_extractor(LifelinesExtractor())
