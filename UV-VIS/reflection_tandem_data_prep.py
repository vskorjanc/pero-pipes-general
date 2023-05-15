# %%
import pandas as pd


from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries.pero_pipes import data_prep as ppdp

# %% [markdown]
# Functions
# %%


def import_file(file):
    df = pd.read_csv(file, sep=", ", index_col=0, engine="python")
    return df


# %%
db = bt.init_thot(__file__)
df = ppdp.import_raw_data(db, import_file, has_date=False)
df = df.apply(lambda x: x / 100)
df.index.name = "wavelength / nm"
df = df.rename(columns={"%R": "reflectance"}, level="param")
df.head()

# %%
_ = bt.export_asset("reflection_tandem_df.pkl", db, bsf.export_pickle, df)
