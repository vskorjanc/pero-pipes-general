# %%
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
import pandas as pd

# %%


def import_file(file):
    df = pd.read_csv(
        file,
        sep="\t",
        skiprows=8,
        names=[
            "time / s",
            "voltage / V",
            "current_density / (mA cm-2)",
            "power / (mW cm-2)",
        ],
        encoding="ISO-8859-15",
    )
    df = df.dropna()
    df = df.drop_duplicates("time / s")
    df["time / s"] = pd.to_numeric(df["time / s"])
    for column in df.columns:
        df[column] = abs(df[column])
    df = df.set_index("time / s")
    df = df[["power / (mW cm-2)", "voltage / V", "current_density / (mA cm-2)"]]
    return df


# %%
db = bt.init_thot(__file__)
df = ppdp.import_raw_data(db, import_file)
df = df.sort_index()

bt.export_asset("MPP_df.pkl", db, pd.to_pickle, df)
df.head()
