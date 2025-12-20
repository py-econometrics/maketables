"""Pytest fixtures for maketables snapshot tests."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def simple_df():
    """Simple DataFrame for basic table tests."""
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        "x": np.random.randn(n),
        "y": np.random.randn(n),
        "group": np.random.choice(["A", "B"], n),
    })


@pytest.fixture
def fitted_model(simple_df):
    """Single fitted pyfixest model."""
    import pyfixest as pf

    # Create deterministic relationship
    np.random.seed(42)
    df = simple_df.copy()
    df["y"] = 2 * df["x"] + np.random.randn(len(df)) * 0.1
    return pf.feols("y ~ x", data=df)


@pytest.fixture
def fitted_models(simple_df):
    """Multiple fitted pyfixest models for multi-column tables."""
    import pyfixest as pf

    np.random.seed(42)
    df = simple_df.copy()
    df["y"] = 2 * df["x"] + np.random.randn(len(df)) * 0.1

    return [
        pf.feols("y ~ x", data=df),
        pf.feols("y ~ x + C(group)", data=df),
    ]


@pytest.fixture
def fitted_model_fe(simple_df):
    """Pyfixest model with fixed effects."""
    import pyfixest as pf

    np.random.seed(42)
    df = simple_df.copy()
    df["y"] = 2 * df["x"] + np.random.randn(len(df)) * 0.1

    # Model with group fixed effects
    return pf.feols("y ~ x | group", data=df)


# Statsmodels fixtures


@pytest.fixture
def statsmodels_ols(simple_df):
    """Statsmodels OLS model."""
    import statsmodels.formula.api as smf

    np.random.seed(42)
    df = simple_df.copy()
    df["y"] = 2 * df["x"] + np.random.randn(len(df)) * 0.1
    return smf.ols("y ~ x", data=df).fit()


@pytest.fixture
def statsmodels_logit(simple_df):
    """Statsmodels Logit model."""
    import statsmodels.formula.api as smf

    np.random.seed(42)
    df = simple_df.copy()
    # Create binary outcome based on x
    df["y_binary"] = (df["x"] > 0).astype(int)
    return smf.logit("y_binary ~ x", data=df).fit(disp=0)


@pytest.fixture
def statsmodels_probit(simple_df):
    """Statsmodels Probit model."""
    import statsmodels.formula.api as smf

    np.random.seed(42)
    df = simple_df.copy()
    # Create binary outcome based on x
    df["y_binary"] = (df["x"] > 0).astype(int)
    return smf.probit("y_binary ~ x", data=df).fit(disp=0)


# Linearmodels fixtures


@pytest.fixture
def panel_df():
    """Panel DataFrame for linearmodels tests."""
    np.random.seed(42)
    n_entities = 20
    n_periods = 5
    n_obs = n_entities * n_periods

    # Create panel structure
    entity_id = np.repeat(np.arange(n_entities), n_periods)
    time_id = np.tile(np.arange(n_periods), n_entities)

    # Entity and time effects
    entity_effects = np.random.randn(n_entities)
    time_effects = np.random.randn(n_periods)

    # Create panel data
    df = pd.DataFrame({
        "entity": entity_id,
        "time": time_id,
        "x1": np.random.randn(n_obs),
        "x2": np.random.randn(n_obs),
    })

    # Create outcome with entity effects
    df["y"] = (
        2 * df["x1"]
        + 0.5 * df["x2"]
        + entity_effects[entity_id]
        + time_effects[time_id]
        + np.random.randn(n_obs) * 0.1
    )

    # Set MultiIndex for panel structure
    df = df.set_index(["entity", "time"])
    return df


@pytest.fixture
def linearmodels_panelols(panel_df):
    """Linearmodels PanelOLS with entity effects."""
    from linearmodels import PanelOLS

    mod = PanelOLS.from_formula("y ~ x1 + x2 + EntityEffects", data=panel_df)
    return mod.fit(cov_type="clustered", cluster_entity=True)


@pytest.fixture
def linearmodels_pooledols(panel_df):
    """Linearmodels PooledOLS (no fixed effects)."""
    from linearmodels import PooledOLS

    mod = PooledOLS.from_formula("y ~ x1 + x2", data=panel_df)
    return mod.fit(cov_type="robust")


@pytest.fixture
def linearmodels_absorbingls():
    """Linearmodels AbsorbingLS with high-dimensional fixed effects."""
    from linearmodels import AbsorbingLS

    np.random.seed(42)
    n_firms = 50
    n_obs = 200

    # Create firm-level data
    firm_id = np.random.choice(n_firms, size=n_obs)
    firm_effects = np.random.randn(n_firms)

    df = pd.DataFrame({
        "firm_id": firm_id,
        "x1": np.random.randn(n_obs),
        "x2": np.random.randn(n_obs),
    })

    df["y"] = 2 * df["x1"] + 0.5 * df["x2"] + firm_effects[firm_id] + np.random.randn(n_obs) * 0.1

    # Fit AbsorbingLS
    mod = AbsorbingLS(
        dependent=df[["y"]],
        exog=df[["x1", "x2"]],
        absorb=df[["firm_id"]],
    )
    return mod.fit(cov_type="robust")


@pytest.fixture
def linearmodels_iv2sls():
    """Linearmodels IV2SLS with instrumental variables."""
    from linearmodels.iv import IV2SLS

    np.random.seed(42)
    n_obs = 200

    # Create IV data: z is instrument for x (endogenous)
    z = np.random.randn(n_obs)  # Instrument
    x_endog = 0.5 * z + np.random.randn(n_obs) * 0.5  # Endogenous regressor
    x_exog = np.random.randn(n_obs)  # Exogenous regressor
    y = 2 * x_endog + 0.5 * x_exog + np.random.randn(n_obs) * 0.1

    df = pd.DataFrame({
        "y": y,
        "x_endog": x_endog,
        "x_exog": x_exog,
        "z": z,
    })

    # IV2SLS: y ~ x_exog + [x_endog ~ z]
    mod = IV2SLS.from_formula("y ~ 1 + x_exog + [x_endog ~ z]", data=df)
    return mod.fit(cov_type="robust")
