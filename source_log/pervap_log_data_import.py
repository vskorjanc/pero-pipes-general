# %%
import pandas as pd
from plotly import express as px
from datetime import datetime

from bix_analysis_libraries import bix_standard_functions as bsf
from thot import ThotProject

# %% [markdown]
#
# ## Formulas

# %%


def get_iso_time(str):
    '''
    Writes the datetime string written by the PeroVap in the ISO format.
    :param str: datetime string as written by the PeroVap
    :returns: ISO datetime string
    '''
    iso = datetime.strptime(str, '%d.%m.%Y %H:%M:%S')
    return iso.isoformat()

# %%


def import_param(file, param):
    df = pd.read_csv(
        file,
        sep=';',
        names=['description', 'time', param, 'validity', 'time_stamp'],
        # index_col='time',
        usecols=[param, 'time'],
        skiprows=[0, 1],
        decimal=','
    )
    df['time'] = df['time'].apply(get_iso_time)
    df = df.set_index('time')
    return df


def import_source_log(file, source, param):
    df = import_param(file, param)
    return bsf.add_level(df, source, 'source', axis=1)


def get_shutter_position(file):
    shut = pd.read_csv(file, sep=';', names=['name', 'time', 'value', 'validity', 'time_stamp'], index_col='time', usecols=['name', 'value', 'time'], skiprows=1, on_bad_lines='skip',
                       decimal=','
                       )
    shut['name'] = shut['name'].where(
        lambda x: x == 'XL_ProVap_Flags_Status_Shutter_Substrat')
    shut = shut.dropna().drop('name', axis=1)
    shut['value'] = shut['value'].where(lambda x: x == 2)
    shut = shut.dropna()
    shut_open = get_iso_time(shut.index.values.min())
    shut_close = get_iso_time(shut.index.values.max())
    return (shut_open, shut_close)

# %% [markdown]
# ## Analysis


# %%
thot = ThotProject(dev_root='../../../evap_pero/data/2021-12-15/evap_log')
assets = thot.find_assets({"type": "evap_log"})
# %%
sources = []
params = []
strings = [
    r'XL_(P_Chamber)0',
    r'XL_(T_Substrat)0',
    r'XL_(T_Chamber_Jacket)0',
    r'XL_(T_Source_Cooling)0'
]
for asset in assets:
    file = asset.file
    # source data
    match = bsf.metadata_from_file_name(file, r'XL_(U?LTE\d)_(.+)0')
    if match:
        df = import_source_log(file, match[1], match[2])
        sources.append(df)
        continue

    # shutter data
    match = bsf.metadata_from_file_name(file, r'XL_Shutter_Pos0')
    if match:
        shut_open, shut_close = get_shutter_position(file)
        continue

    for string in strings:
        match = bsf.metadata_from_file_name(file, string)
        if match:
            df = import_param(file, match[1])
            params.append(df)


sources = pd.concat(sources, axis=1)
sources = sources.sort_index(axis=1)

params = pd.concat(params, axis=1)
params.head()
# %%
# remove inactive sources
for source, data in sources.groupby('source', axis=1):
    if data[source, 'Rate'].mean() == 0:
        sources = sources.drop(source, axis=1)
sources.head()
# %%
props = {
    'file': 'source_log_df.pkl',
    'type': 'source_log_df',
    'tags': ['source_log', 'df']
}
asset_path = thot.add_asset(props, 'source_log_df')
pd.to_pickle(df, asset_path, protocol=4)

# %%
for column in df.columns.values:
    median = df[column].median()
    (source, param) = column
    df[source, f'{param}_norm'] = df[column] / median
df.head()

# %%
for source, data in df.groupby('source', axis=1):
    data = data.droplevel('source', axis=1)
    fig = px.line(
        data,
        y=['Rate_norm', 'I_norm', 'T_AV_norm', 'T_SP_norm'],
        hover_data=['Rate', 'I', 'T_AV', 'T_SP'],
        title=source
    )
    fig.add_vrect(
        x0=shut_open,
        x1=shut_close,
        fillcolor="LightSalmon",
        opacity=0.5,
        layer="below",
        line_width=0,
    )

    plot_props = {
        'file': f'{source}_log_plot.html',
        'type': 'source_log_plot',
        'tags': ['source_log', 'plot']
    }
    asset_path = thot.add_asset(plot_props, f'{source}_log_plot')
    fig.write_html(asset_path, include_plotlyjs='cdn')
