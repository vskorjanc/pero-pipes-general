# %%
import pandas as pd

from bix_analysis_libraries import thot as bt
from thot import ThotProject
from bix_analysis_libraries import bix_standard_functions as bsf

# %% [markdown]
# ## Data import

# %%
thot = ThotProject(dev_root='../../../../evap_pero/data/2021-12-06_1/JV_map')
data = bt.find_raw_assets(thot)

# %%
dfs = []
for datum in data:
    df = pd.read_csv(datum.file, index_col=0, delimiter='\t',
                     header=8, nrows=9, usecols=range(13),  encoding='ISO-8859-15')
    df.columns = pd.MultiIndex.from_product(
        [['a', 'b', 'c', 'd', 'e', 'f'], ['for', 'rev']], names=['pixel', 'direction'])
    df = bsf.add_level(df, datum.name, 'substrate', axis=1)
    dfs.append(df)
df = pd.concat(dfs, axis=1)
df.head()

# %%
df = df.transpose()
df = df.drop('P_MPP [mW/cm²]:', axis=1)
df.columns = ['J_sc', 'V_oc', 'FF', 'PCE', 'J_MPP', 'V_MPP', 'R_ser', 'R_par']
df.head()

# %% [markdown]
# ## Filter and average

# %%
# remove FF > 90 %
df['FF'] = df['FF'].where(lambda x: x < 90)
# make J_sc and J_MPP positive
df['J_sc'] = -1 * df['J_sc']
df['J_MPP'] = -1 * df['J_MPP']

# %%
df_mean = df.groupby(level=['substrate', 'pixel']).mean()
df_mean.head()

# %% [markdown]
# ## Export

# %%
props = {
    'file': 'JV_metrics.pkl',
    'type': 'JV_metrics',
    'tags': ['JV', 'metrics']
}
asset_path = thot.add_asset(props, 'JV_metrics')
pd.to_pickle(df_mean, asset_path)
