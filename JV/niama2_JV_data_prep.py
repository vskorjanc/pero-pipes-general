# %%
import pandas as pd

from bix_analysis_libraries import thot as bt
from thot import ThotProject
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
# %%


def extract_direction(df):
    df.columns = df.columns.str.split('_', expand=True)
    df = df.rename_axis(('pixel', 'direction'), axis=1)
    return df


def import_metrics(file):
    df = pd.read_csv(
        file,
        index_col=0,
        delimiter='\t',
        header=8,
        nrows=9,
        encoding='ISO-8859-15'
    )
    # remove last column
    df = df.iloc[:, :-1]
    df = extract_direction(df)
    df = df.drop('P_MPP [mW/cm²]:')
    df.index = ['J_sc', 'V_oc', 'FF', 'PCE',
                'J_MPP', 'V_MPP', 'R_ser', 'R_par']
    return df


def import_scans(file):
    df = pd.read_csv(
        file,
        index_col=0,
        delimiter='\t',
        header=19,
        skiprows=[20],
        encoding='ISO-8859-15'
    )
    df = df.iloc[:, :-1]
    df = extract_direction(df)
    return df


def remove_duplicates(
    df: pd.DataFrame
):
    '''
    Keeps only the last measurement in case multiple measurements are saved.
    :rtype: pd.DataFrame
    '''
    df = df[~df.index.duplicated(keep='last')]
    return df

# %% [markdown]
# ## Data import


# %%
db = ThotProject(
    dev_root='../../../data/2021-11-16/JV')
# %%
asset = db.find_asset({'type': ''})
scans = ppdp.import_raw_data(
    db,
    import_scans,
    has_pixel=False,
    rename_axis=False,
    sort_columns=True
)
scans = remove_duplicates(scans.T).T
scans = scans.stack(['date', 'pixel', 'direction'])
bt.export_asset('JV_scans.pkl', db, pd.to_pickle, scans)
scans.head()
# %%
raw_metrics = ppdp.import_raw_data(
    db,
    import_metrics,
    has_pixel=False,
    rename_axis=False,
    sort_columns=True
)
raw_metrics = raw_metrics.T
# remove duplicate values
raw_metrics = remove_duplicates(raw_metrics)
raw_metrics.head()
# %% [markdown]
# ## Filter and average

# %%
# remove FF > 90 %
raw_metrics['FF'] = raw_metrics['FF'].where(lambda x: x < 90)
# make J_sc and J_MPP positive
raw_metrics['J_sc'] = -1 * raw_metrics['J_sc']
raw_metrics['J_MPP'] = -1 * raw_metrics['J_MPP']

# %%
metrics = raw_metrics.groupby(level=['substrate', 'pixel']).mean()
metrics.head()

# %% [markdown]
# ## Export

# %%
# %%
bt.export_asset('raw_JV_metr.pkl', db, pd.to_pickle, raw_metrics)
bt.export_asset('JV_metrics.pkl', db, pd.to_pickle, metrics)
