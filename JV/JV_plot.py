# %%
import sys
import numpy as np
from plotly import express as px
import plotly.graph_objects as go
from plotly import graph_objects as go
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
# %%
db = bt.init_thot(__file__)
scans = ppdp.import_formatted_data(db, {'type': 'JV_scans'})
scans.head()


# %%
container = db.find_container({'_id': db.root})
# %%
colors = px.colors.qualitative.Plotly
presets = {
    'a': colors[0],
    'b': colors[1],
    'c': colors[2],
    'd': colors[3],
    'e': colors[4],
    'f': colors[5],
    'for': None,
    'rev': 'dash'
}
# %%


def invert_groups(groups):
    '''
    Inverts 'group':[<substrates>] pairs in dictionary.
    :param groups: Dictionary with 'group':[<substrates>] pairs.
    :returns: Dictionary with 'substrate':'group' pairs. 
    '''
    inverted_groups = {}
    for group, substrates in groups.items():
        if not isinstance(substrates, list):
            substrates = [substrates]
        for substrate in substrates:
            inverted_groups[substrate] = group
    return inverted_groups


def plot_single_scan(data, visible, presets):
    traces = []
    for (pxl, dr), datum in data.groupby(['pixel', 'direction']):
        c = presets[pxl]
        d = presets[dr]
        scat = go.Scatter(
            x=datum.index.get_level_values('Voltage'),
            y=datum,
            line_color=c,
            line_dash=d,
            name=f'{pxl}\t{dr}',
            visible=visible
        )
        traces.append(scat)
    return traces


def plot_single_metric(data, visible):
    traces = []
    for di, datum in data.groupby('direction'):
        pxl = datum.index.get_level_values('pixel')
        pxl = [f'pixel {px}' for px in pxl]
        box = go.Box(
            x=datum.index.get_level_values('substrate'),
            y=datum,
            boxpoints='all',
            name=di,
            hovertext=pxl,
            visible=visible
        )
        traces.append(box)
    return traces


def plot_single_grouped_metric(data, visible):
    traces = []
    pxls = data.index.get_level_values('pixel')
    subs = data.index.get_level_values('substrate')
    hovertext = [f'{sub}_{pxl}' for (sub, pxl) in zip(subs, pxls)]
    box = go.Box(
        x=data.index.get_level_values('group'),
        y=data,
        boxpoints='all',
        hovertext=hovertext,
        visible=visible
    )
    traces.append(box)
    return traces


# %%
fig = bp.multilayer_plot(scans, plot_single_scan, presets=presets)
fig.update_layout(
    xaxis_title="Voltage / V",
    yaxis_title="Current density / mA cm<sup>&#8722;2</sup>",
)
# fig.add_hline(y=0)
# fig.add_vline(x=0)
# fig.show()
bt.export_asset('JV-scans_plot.html', db, bp.export_plotly, fig)
# %%
metrics = ppdp.import_formatted_data(db, {"type": "raw_JV_metr"})
fig2 = bp.multilayer_plot(metrics, plot_single_metric,
                          params=('J_sc', 'V_oc', 'FF', 'PCE'))
fig2.update_layout(
    boxmode='group'  # group together boxes of the different traces for each value of x
)
# fig.show()
# %%
bt.export_asset('substrate_boxplot.html', db, bp.export_plotly, fig2)
# %%
if 'groups' in container.metadata:
    groups = container.metadata['groups']
    inverted_groups = invert_groups(groups)

    def get_group(substrate, inverted_groups):
        if substrate in inverted_groups:
            return inverted_groups[substrate]
        else:
            return np.nan

    metrics['group'] = [get_group(substrate, inverted_groups)
                        for substrate in metrics.index.get_level_values('substrate')]

else:
    metrics['group'] = metrics.index.get_level_values('substrate')

metrics = metrics.set_index('group', append=True)
metrics.head()
# %%
# calculate the mean of forward and backward scan
mean = metrics.groupby(['substrate', 'pixel', 'group']).aggregate('mean')
# hide points with V_oc < 0.2 V
mean = mean.where(lambda x: x['V_oc'] > 0.2).dropna()
# %%
# %%
fig3 = bp.multilayer_plot(mean, plot_single_grouped_metric,
                          params=('J_sc', 'V_oc', 'FF', 'PCE'))
bt.export_asset('grouped_boxplot.html', db, bp.export_plotly, fig3)
# %%

# def mask(x):
# if x > (0.2 * x.median()):
# return x
# else:
# return np.nan
# mask = mean.groupby(['substrate', 'pixel']).apply(
# lambda x: 0.2 * x.median() < x)
# masked = mean.where(mask).dropna()
# masked.head()
