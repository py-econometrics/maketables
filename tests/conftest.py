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
