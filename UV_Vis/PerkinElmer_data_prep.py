# %% [markdown]
# TODO import full stack data separately (e.g. VikA01_a)

# %%
import pandas as pd

from thot import ThotProject
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import bix_standard_functions as bsf
from bric_analysis_libraries.pl import pl_data_prep as pdp

# %%
thot = ThotProject(dev_root='../../../../evap_pero/data/2021-12-15/UV_VIS')
reflection = bt.find_raw_assets(thot)
transmission = bt.find_raw_assets(thot)

# %%
data = []
for asset in [*reflection, *transmission]:
    substrate = bsf.metadata_from_file_name(
        asset.file,
        r'(.+)\.Probe\.Rohdaten'
    ).group(1)
    datum = pd.read_csv(asset.file, sep=';', index_col=0, decimal=',')
    datum = bsf.add_level(datum, substrate, 'substrate', axis=1)
    data.append(datum)
df = pd.concat(data, axis=1)
df.head()

# %%
e_df = pdp.index_to_energy(df)
e_df.columns.names = ['substrate', 'param']
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
asset_path = thot.add_asset(props, 'UV-VIS_df')
pd.to_pickle(e_df, asset_path, protocol=4)
