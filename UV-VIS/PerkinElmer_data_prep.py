# %%
import pandas as pd


from bric_analysis_libraries.pl import pl_data_prep as pdp
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp

# %% [markdown]
# Functions
# %%


def import_file(file):
    df = pd.read_csv(
        file,
        sep=';',
        index_col=0,
        decimal=','
    )
    return df


# %%
db = bt.init_thot(__file__)
df = ppdp.import_raw_data(db, import_file)
df.head()

# %%
e_df = pdp.index_to_energy(df)
e_df.index.name = 'energy/eV'
e_df = e_df.rename(
    columns={
        ' %R': 'reflectance',
        ' %T': 'transmittance'
    },
    level='param'
)
e_df = e_df.apply(lambda x: x / 100)
e_df.head()


# %%
props = {
    'file': 'UV-VIS_df.pkl',
    'type': 'UV-VIS_df',
    'tags': ['UV-VIS', 'df']
}
asset_path = db.add_asset(props, 'UV-VIS_df')
pd.to_pickle(e_df, asset_path, protocol=4)
