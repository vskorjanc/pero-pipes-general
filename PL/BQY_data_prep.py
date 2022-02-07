# %% [markdown]
# # PL data prep
# 1. Raw PL data import
# 2. Calibrating and calculating flux
# 3. Conversion from wavelength to energy

# %%
import pandas as pd
import re
import os.path

from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries.pl import pl_data_prep as bplp
from thot import ThotProject

# %%


def open_row_file(file):
    with open(file, 'r') as f:
        return eval(f.readline())


# opening calibration and dark offset curves
offset = open_row_file('calib/darkAsRow.txt')
calib = open_row_file('calib/calibSplitterStellar_pro_asRow.txt')

# %%
thot = ThotProject(dev_root='../../temp/PL_test')
assets = thot.find_assets({"type": "PL_spectrum"})

# %% [markdown]
# ## Data import

# %%
dfs = []
for asset in assets:
    with open(asset.file) as fd:
        headers = [next(fd) for i in range(4)]
        int_time = int(headers[3])
        df = pd.read_csv(fd, sep='\t', names=[
            'wavelength', 'counts/s'], index_col=0)
    df['counts/s'] = df['counts/s'] * 1000 / int_time
    file = os.path.basename(asset.file)
    try:  # find measurement data
        pattern = re.compile('(.+)P(\d*[a-f]*)_\d+ms\.txt')
        match = re.match(pattern, file)
        df = bsf.add_levels(df, [match[1], match[2]], [
                            'substrate', 'pixel'], axis=1)
    except TypeError:  # find reference data
        pattern = re.compile('(white)_\d+ms\.txt')
        match = re.match(pattern, file)
        df = bsf.add_levels(df, ['ref', ''], ['substrate', 'pixel'], axis=1)
    dfs.append(df)
df = pd.concat(dfs, axis=1)
df = df.sort_index(axis=1)
df = df.rename_axis(columns=['substrate', 'pixel', 'param'])
df.head()

# %%
flux_df = bplp.calc_photon_flux(df, calib, offset, area=0.000012)
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
asset_path = thot.add_asset(props, 'PL_df')
pd.to_pickle(flux_df, asset_path, protocol=4)
