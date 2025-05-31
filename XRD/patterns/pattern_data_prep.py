# %%
import pandas as pd
import glob
import os.path
from bix_analysis_libraries import bix_standard_functions as bsf
import numpy as np

# %%


def import_txt(file):
    # regex for 2 or more spaces necessary because of `d (A)` column
    df = pd.read_csv(file, sep=r"\s{2,}", usecols=["2θ", "I"], engine="python")
    df = df.mask(df == "-1.#IND0").dropna()
    df = df.rename({"2θ": "2theta", "I": "intensity"}, axis=1)
    df = df.astype(np.float32)
    df = df.where(df["2theta"] < 60).where(df["2theta"] > 8).dropna()
    df["2theta"] = df["2theta"].round(2)
    return df


def add_compound_level(df, file):
    compound, _ = os.path.splitext(file)
    df = bsf.add_level(df, compound, "compound", axis=1)
    return df


def normalize_and_reindex(df):
    # sum up multiple values for 2theta and normalize
    df = df.groupby("2theta").aggregate("sum")
    df = df.apply(lambda x: x / x.max())
    df = df.reindex(
        np.linspace(5, 80, 5201), method="nearest", fill_value=0, tolerance=0.005
    )
    return df


def import_xy(file):
    df = pd.read_csv(file, index_col=0, sep="\s+", names=["2theta", "intensity"])
    return df


def import_and_append(import_file, glob_pattern, lst):
    files = glob.glob(glob_pattern)
    for file in files:
        df = import_file(file)
        df = normalize_and_reindex(df)
        df = add_compound_level(df, file)
        lst.append(df)


# %%
dfs = []
types = [[import_txt, "*.txt"], [import_xy, "*.xy"]]
for if_glb in types:
    import_and_append(*if_glb, dfs)
df = pd.concat(dfs, axis=1, sort=True)
df.head()

# %%
pd.to_pickle(df, "patterns.pkl")
