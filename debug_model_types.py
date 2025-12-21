"""Debug script to check logit model class names"""

import numpy as np
import pandas as pd
import statsmodels.api as sm

np.random.seed(42)
n = 200
df = pd.DataFrame({
    'const': 1,
    'x1': np.random.randn(n),
    'x2': np.random.randn(n),
})
df['y'] = (np.random.randn(n) + df['x1'] > 0).astype(int)

logit = sm.Logit(df['y'], df[['const', 'x1', 'x2']]).fit(disp=0)
probit = sm.Probit(df['y'], df[['const', 'x1', 'x2']]).fit(disp=0)
ols = sm.OLS(df['y'], df[['const', 'x1', 'x2']]).fit()

print(f"Logit result type: {type(logit).__name__}")
print(f"  has model attr: {hasattr(logit, 'model')}")
if hasattr(logit, 'model'):
    print(f"  model class: {type(logit.model).__name__}")

print(f"\nProbit result type: {type(probit).__name__}")
print(f"  has model attr: {hasattr(probit, 'model')}")
if hasattr(probit, 'model'):
    print(f"  model class: {type(probit.model).__name__}")

print(f"\nOLS result type: {type(ols).__name__}")
print(f"  has model attr: {hasattr(ols, 'model')}")
if hasattr(ols, 'model'):
    print(f"  model class: {type(ols.model).__name__}")
