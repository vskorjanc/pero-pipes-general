# %%
import pandas as pd
import glob
import os.path
from bix_analysis_libraries import bix_standard_functions as bsf
import numpy as np
# %%


def import_file(file):
    # regex for 2 or more spaces necessary because of `d (A)` column
    df = pd.read_csv(
        file,
        sep=r'\s{2,}',
        usecols=['2θ', 'I'],
        engine='python'
    )
    df = df.mask(df == '-1.#IND0').dropna()
    df = df.rename({'2θ': '2theta', 'I': 'intensity'}, axis=1)
    df = df.astype(np.float32)
    df = df.where(df['2theta'] < 60).where(df['2theta'] > 8).dropna()
    df['2theta'] = df['2theta'].round(2)
    return df


def add_compound_level(df, file):
    compound, _ = os.path.splitext(file)
    df = bsf.add_level(df, compound, 'compound', axis=1)
    return df


# %%
files = glob.glob('*.txt')
dfs = []
for file in files:
    df = import_file(file)
    # sum up multiple values for 2theta and normalize
    df = df.groupby('2theta').aggregate('sum')
    df = df.apply(lambda x: x / x.max())
    df = df.reindex(
        np.linspace(8, 60, 5201),
        method='nearest',
        fill_value=0,
        tolerance=0.004
    )
    df = add_compound_level(df, file)
    dfs.append(df)
df = pd.concat(dfs, axis=1, sort=True)
df.head()
# %%
pd.to_pickle(df, 'patterns.pkl')
