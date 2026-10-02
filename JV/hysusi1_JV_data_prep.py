# %%
import pandas as pd

from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp

# %%


def extract_direction(df):
    df.columns = df.columns.str.split("_", expand=True)
    df = df.rename_axis(("pixel", "direction"), axis=1)
    return df


def import_scans(file):
    df = pd.read_csv(
        file,
        index_col=0,
        delimiter="\t",
        header=29,
        skiprows=[30],
        encoding="ISO-8859-15",
    )
    print(df.head())
    df = extract_direction(df)
    if df.columns.get_level_values("pixel").any() != "j":
        # remove last column
        df = df.iloc[:, :-1]
    return df


def remove_duplicates(df: pd.DataFrame):
    """
    Keeps only the last measurement in case multiple measurements are saved.
    :rtype: pd.DataFrame
    """
    df = df[~df.index.duplicated(keep="last")]
    return df


# %% [markdown]
# ## Data import


# %%
db = bt.init_thot(__file__)
# %%
pattern = r"^([^_]+)"
scans = ppdp.import_raw_data(
    db, import_scans, rename_axis=False, sort_columns=True, pattern=pattern
)
scans = remove_duplicates(scans.T).T
scans = scans.stack(["date", "pixel", "direction"], future_stack=True)
bt.export_asset("JV_scans.pkl", db, pd.to_pickle, scans)
scans.head()
# %%


def import_metrics(file):
    df = pd.read_csv(
        file, index_col=0, delimiter="\t", header=18, nrows=9, encoding="ISO-8859-15"
    )
    try:
        df = extract_direction(df)
        # remove last column
        df = df.iloc[:, :-1]
    except ValueError:
        pass
    df = df.drop("P_MPP [mW/cm²]:")
    df.index = ["J_sc", "V_oc", "FF", "PCE", "J_MPP", "V_MPP", "R_ser", "R_par"]
    df = df.apply(lambda x: abs(x))
    df.columns.name = "direction"
    return df


raw_metrics = ppdp.import_raw_data(
    db, import_metrics, rename_axis=False, sort_columns=True, pattern=pattern
)
raw_metrics = raw_metrics.T
# remove duplicate values
raw_metrics = remove_duplicates(raw_metrics)
raw_metrics.head()
# %% [markdown]
# ## Filter and average

# %%
# remove FF > 90 %
raw_metrics["FF"] = raw_metrics["FF"].where(lambda x: x < 90)
if "pixel" in raw_metrics.index.names:
    # make J_sc and J_MPP positive
    raw_metrics["J_sc"] = abs(raw_metrics["J_sc"])
    raw_metrics["J_MPP"] = abs(raw_metrics["J_MPP"])

    # multiply R_par with 100
    raw_metrics["R_par"] *= 1000
    metrics = raw_metrics.groupby(level=["substrate", "pixel"]).mean()
    metrics.head()
    ppdp.pickle_w_markdown(metrics, "JV_metrics", db, floatfmt=".2f")

ppdp.pickle_w_markdown(raw_metrics, "raw_JV_metrics", db, floatfmt=".2f")
