# %%
from plotly import express as px
import plotly.graph_objects as go
from plotly import graph_objects as go
from thot import ThotProject
from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
# %%
db = ThotProject(dev_root='../../../data/2021-11-16/JV')
scans = ppdp.import_formatted_data(db, {'type': 'JV_scans'})
scans.head()


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


# %%
fig = bp.multilayer_plot(scans, plot_single_scan, presets=presets)
fig.update_layout(
    xaxis_title="Voltage / V",
    yaxis_title="Current density / mA cm<sup>&#8722;2</sup>",
)
fig.add_hline(y=0)
fig.add_vline(x=0)
# fig.show()
bt.export_asset('JV-scans_plot.html', db, bp.export_plotly, fig)
# %%
metrics = ppdp.import_formatted_data(db, {"type": "raw_JV_metr"})
metrics.head()
# %%


# %%
fig2 = bp.multilayer_plot(metrics, plot_single_metric,
                          params=('J_sc', 'V_oc', 'FF', 'PCE'))
fig2.update_layout(
    boxmode='group'  # group together boxes of the different traces for each value of x
)
# fig.show()
# %%
bt.export_asset('batch_boxplot.html', db, bp.export_plotly, fig2)
