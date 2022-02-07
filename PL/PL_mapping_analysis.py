# %%
import pandas as pd
import numpy as np
import sys

from plotly import graph_objects as go
from plotly import express as px

from thot import ThotProject
from bric_analysis_libraries.pl import pl_analysis as pla
from bix_analysis_libraries import bix_standard_functions as bsf
# from bric_analysis_libraries.pl import pl_data_prep as pldp

# %% [markdown]
# ## Functions

# %%
# TODO make into a function and add to the BSF or even better put the plots into the plotting library


def plot_PL_params(df, params):
    '''
    Plots PL params as 3D surface and heatmap for data exploration.
    :param df: Pandas DataFrame indexed by y cordinate in Index, and x coordinate, as well as params in Columns.
    :param params: List of params from Columns to plot.
    :returns: plotly.graph_objects.Figure instance.
    '''
    fig = go.Figure()

    def add_trace(fig, data, visible=True):
        fig.add_trace(
            go.Heatmap(
                x=data.columns.get_level_values(0).tolist(),
                y=data.index.values.tolist(),
                z=data,
                visible=visible
            )
        )

    lpr = len(params)
    bl = []
    for (nr, param) in enumerate(params):
        if nr == 0:
            add_trace(fig, df[param])
        else:
            add_trace(fig, df[param], visible=False)
        tfl = lpr * [False]
        tfl[nr] = True
        bl.append(
            dict(
                args=[{'visible': tfl}],
                label=param,
                method='update'
            )
        )
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=list([
                    dict(
                        args=["type", "heatmap"],
                        label="Heatmap",
                        method="restyle"
                    ),
                    dict(
                        args=["type", "surface"],
                        label="3D Surface",
                        method="restyle"
                    ),
                ]),
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.1,
                yanchor="top"
            ),
            dict(
                buttons=bl,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.37,
                xanchor="left",
                y=1.1,
                yanchor="top"
            ),
        ]
    )
    return (fig)

# %% [markdown]
# ## Data prep


# %%
thot = ThotProject(dev_root='../../data/batch_01/PL_mapping')
df = thot.find_asset({'type': 'PL_mapping_df'})
df = pd.read_pickle(df.file)
# smooth out w/ rolling median
df = df.groupby(level=['x/cm', 'y/cm']).rolling(8,
                                                center=True).median().droplevel(level=[0, 1])
df = df.dropna()
df.head()

# %%
p_df = []
for (x, y), data in df.groupby(['x/cm', 'y/cm']):
    data = data.copy()
    if data.iloc[0]['intensity'] == 0:
        continue
    data = data.droplevel(('x/cm', 'y/cm'))
    params = pla.peak_analysis(data, start=2, end=1.4)
    params = bsf.add_levels(params, (x, y), ['x/cm', 'y/cm'])
    p_df.append(params)

p_df = pd.concat(p_df)
p_df.index = p_df.index.droplevel(-1)

# %%
p_df['log(area)'] = np.log(p_df.area)
p_df.head()

# %% [markdown]
# ## Exploration plots

# %%
params = p_df.columns.values.tolist()
fig = plot_PL_params(p_df.unstack(0), params)
fig.update_layout(
    # width=800,
    # height=900,
    # autosize=True,
    margin=dict(t=100, b=0, l=0, r=0),
    xaxis_title='x',
    yaxis_title='y'
)
# fig.show ()

# %%
plot_props = {
    'file': 'PL_mapping_param_plot.html',
    'type': 'PL_mapping_param_plot',
    'tags': ['PL', 'plot']
}
asset_path = thot.add_asset(plot_props, 'PL_mapping_param_plot')
fig.write_html(asset_path, include_plotlyjs='cdn')

# %%
sys.exit()

# %% [markdown]
# ---

# %%
temp = df.loc[7.1369, 1.5515, :]
temp.index = temp.index.droplevel([0, 1])
px.scatter(temp)
