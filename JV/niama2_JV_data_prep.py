# %%
import pandas as pd

from thot import ThotProject
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
# %%


def import_file(file):
    df = pd.read_csv(
        file,
        index_col=0,
        delimiter='\t',
        header=8,
        nrows=9,
        encoding='ISO-8859-15'
    )
    df = df.iloc[:, :-1]
    df.columns = df.columns.str.split('_', expand=True)
    df = df.rename_axis(('pixel', 'direction'), axis=1)
    df = df.drop('P_MPP [mW/cm²]:')
    df.index = ['J_sc', 'V_oc', 'FF', 'PCE',
                'J_MPP', 'V_MPP', 'R_ser', 'R_par']
    return df
# %% [markdown]
# ## Data import


# %%
db = ThotProject(
    dev_root='../../../data/4_source_FACsPbIBr/2022-01-06_Paul/JV')
# %%
df = ppdp.import_raw_data(
    db,
    import_file,
    has_pixel=False,
    rename_axis=False,
    sort_columns=True
)
df = df.T
# remove duplicate values
df = df[~df.index.duplicated(keep='last')]
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
asset_path = db.add_asset(props, 'JV_metrics')
pd.to_pickle(df_mean, asset_path)
