# %%
import pandas as pd
from thot import ThotProject

from bric_analysis_libraries.pl import pl_data_prep as pdp
from bix_analysis_libraries import bix_standard_functions as bsf

# %%
thot = ThotProject(dev_root='../../../../evap_pero/data/2021-11-16/EQE')
assets = thot.find_assets({'type': 'EQE_spectrum'})

# %%
df = []
for asset in assets:
    match = bsf.metadata_from_file_name(
        asset.file, '(.+)_([a-f])', as_list=True)
    data = pd.read_csv(
        asset.file,
        sep='\t',
        skiprows=range(10),
        names=['wavelength/nm', 'measured', 'EQE'],
        usecols=['wavelength/nm', 'EQE'],
        index_col=0
    )
    data = bsf.add_levels(data, match, names=['substrate', 'pixel'], axis=1)
    df.append(data)
df = pd.concat(df, axis=1)
df = df.apply(lambda x: x / 100)
df.head()


# %%
e_df = pdp.index_to_energy(df).sort_index()
e_df.columns.names = ['substrate', 'pixel', 'param']
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
