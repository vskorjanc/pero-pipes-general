# %% [markdown]
# # PL data prep
# 1. Raw PL data import
# 2. Calibrating and calculating flux
# 3. Conversion from wavelength to energy

# %%
import pandas as pd

from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries.pl import pl_data_prep as bplp


# %% [markdown]
# Functions
# %%


def import_file(file):
    with open(file) as fd:
        headers = [next(fd) for i in range(4)]
        int_time = int(headers[3])
        df = pd.read_csv(fd, sep='\t', names=[
            'wavelength', 'counts/s'], index_col=0)
    df['counts/s'] = df['counts/s'] * 1000 / int_time
    return df
# %% [markdown]
# ## Data import


# %%
db = bt.init_thot(__file__)
assets = bt.find_assets(db)
dfs = []
for asset in assets:
    df = import_file(asset.file)
    match = ppdp.get_substrate_name(asset.file)
    if match[0] == 'white':
        df = bsf.add_levels(df, ['white', ''], ['substrate', 'pixel'], axis=1)
    else:
        df = bsf.add_levels(df, [match[0], match[1]], [
                            'substrate', 'pixel'], axis=1)
    dfs.append(df)
df = pd.concat(dfs, axis=1)
df = df.sort_index(axis=1)
df = df.rename_axis(columns=['substrate', 'pixel', 'param'])
df.head()

# %%
calib = bt.import_global_asset(
    db,
    a_type='BQY_calib_df',
    a_path=r"root:/..\\scripts\\common\\PL\\calib\\BQY_calib_df.pkl",
    dev_path='calib/BQY_calib_df.pkl',
)
calib.head()
# %%
flux_df = bplp.calc_photon_flux(df, calib, area=0.000012)
flux_df = bplp.df_to_energy(flux_df)
flux_df = flux_df.rename(
    columns={'counts/s': 'flux [photons/(m2 s eV)]'},
    level='param'
)
flux_df.head()

# %%
props = {
    'file': 'PL_df.pkl',
    'type': 'PL_df',
    'tags': ['PL', 'df']
}
asset_path = db.add_asset(props, 'PL_df')
pd.to_pickle(flux_df, asset_path, protocol=4)
