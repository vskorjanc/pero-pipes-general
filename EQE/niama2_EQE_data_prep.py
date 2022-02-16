# %%
import pandas as pd
from thot import ThotProject

from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bric_analysis_libraries.pl import pl_data_prep as pdp

# %% [markdown]
# Functions
# %%


def import_file(file):
    df = pd.read_csv(
        file,
        sep='\t',
        skiprows=range(10),
        names=['wavelength/nm', 'measured', 'EQE'],
        usecols=['wavelength/nm', 'EQE'],
        index_col=0
    )
    return df


# %%
thot = ThotProject(dev_root='../../../../evap_pero/data/2021-11-16/EQE')
df = ppdp.import_raw_data(thot, import_file)
df = df.apply(lambda x: x / 100)
df.head()


# %%
e_df = pdp.index_to_energy(df).sort_index()
e_df.index.name = 'energy/eV'
e_df.head()

# %%
props = {
    'file': 'EQE_df.pkl',
    'type': 'EQE_df',
    'tags': ['EQE', 'df']
}
asset_path = thot.add_asset(props, 'EQE_df')
pd.to_pickle(e_df, asset_path, protocol=4)
