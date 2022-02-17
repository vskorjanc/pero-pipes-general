# %% [markdown]
# # PL data prep
# 1. Raw PL data import
# 2. Calibrating and calculating flux
# 3. Conversion from wavelength to energy

# %%
import pandas as pd

from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries.pl import pl_data_prep as bplp
from thot import ThotProject

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
db = ThotProject(dev_root='../../../../evap_pero/temp/PL_test')
df = ppdp.import_raw_data(db, import_file)
df.head()

# %%
calib = db.find_asset({'type': 'BQY_calib_df'})
calib = pd.read_pickle(calib.file)
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
