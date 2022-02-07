# %%
import pandas as pd
import numpy as np

from plotly import express as px
from plotly import graph_objects as go

from thot import ThotProject

# %% [markdown]
# ## Functions

# %%


def multilayer_heatmap(df, params):
    '''
    Plots PL params as heatmap for data exploration.
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
    return fig


def substrate_coordinate(substrate, substrate_array):
    '''
    Returns the x and y position of the array according to the numbering within the PeroVap machine.
    :param substrate: substrate name
    :param substrate_array: NumPy array of substrates
    :returns: tuple containing x and y coordinate
    '''
    coord = np.asarray(np.where(substrate_array == substrate)).T[0]
    return (tuple(coord))


def pixel_coordinate(pix, substrate_coord):
    '''
    Expands the substrate position to accomodate for the array of pixels.
    :param pixel: pixel letter
    :param substrate_coord: tuple of x and y coordinates of substrate
    :returns:tuple containing x and y coordinate of the pixel
    '''
    x, y = substrate_coord
    x *= 3
    y *= 2
    if pix == 'a':
        return (x, y)
    elif pix == 'b':
        return (x, y + 1)
    elif pix == 'c':
        return (x + 1, y)
    elif pix == 'd':
        return (x + 1, y + 1)
    elif pix == 'e':
        return (x + 2, y)
    elif pix == 'f':
        return (x + 2, y + 1)
    else:
        return ValueError('Non-valid pixel name')


# %%
thot = ThotProject(dev_root='../../data/2021-12-06_1/JV_map')
data = thot.find_asset({'type': 'JV_mean'})
container = thot.find_container({'type': 'JV_map'})

# %%
df = pd.read_pickle(data.file)
df.head()

# %% [markdown]
# ## Data prep

# %%
# take the position from the metadata, else assume the cells are ordered and the shape is square
if 'positions' in container.metadata:
    dimension = container.metadata['dimension']
    dimension = [int(x) for x in dimension]
    positions = container.metadata['positions']
    x = dimension[0]
    y = dimension[1]
    subs = [''] * (x*y)
    for key, value in positions.items():
        k = int(key)
        subs[k] = value
    subs = np.reshape(subs, dimension)
else:
    subs = df.index.get_level_values('substrate').unique()
    dimension = [int(np.sqrt(len(subs)))] * 2
    subs = np.reshape(subs, dimension)


map_df = []
for (sub, pix), data in df.groupby(['substrate', 'pixel']):
    xy = substrate_coordinate(sub, subs)
    x, y = pixel_coordinate(pix, xy)

    # invert x and y
    x = 3*dimension[0] - 1 - x
    y = 2*dimension[1] - 1 - y

    data = data.copy()
    data.index = pd.MultiIndex.from_tuples([(x, y)], names=['x', 'y'])
    map_df.append(data)
map_df = pd.concat(map_df)
map_df.head()


# %% [markdown]
# ## Plot

# %%
m_df = map_df.unstack(0)
fig = multilayer_heatmap(m_df, params=('PCE', 'FF', 'V_oc', 'J_sc'))

# add lines to the plot to separate the pixels
x, y = dimension
x_max = x * 3
y_max = y * 2
y = 1.5
while y < y_max:
    fig.add_hline(y=y, line_color='white')
    y += 2
x = 2.5
while x < x_max:
    fig.add_vline(x=x, line_color='white')
    x += 3
fig.update_xaxes(range=[-0.5, x_max - 0.5])
fig.update_yaxes(range=[-0.5, y_max - 0.5])
fig


# %%
props = {
    'file': 'JV_map_plot.html',
    'type': 'JV_map_plot',
    'tags': ['JV', 'map', 'plot']
}
asset_path = thot.add_asset(props, 'JV_map_plot')
fig.write_html(asset_path, include_plotlyjs='cdn')
