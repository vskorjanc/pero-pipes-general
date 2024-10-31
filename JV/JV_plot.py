# %%
import numpy as np
import pandas as pd
from plotly import express as px
import plotly.graph_objects as go
from plotly import graph_objects as go
from plotly.subplots import make_subplots
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries import bix_standard_functions as bsf

# %%
db = bt.init_thot(__file__)
scans = ppdp.import_formatted_data(db, {"type": "JV_scans"})
scans.head()


# %%
container = db.find_container({"_id": db.root})
# %%
colors = px.colors.qualitative.Plotly
presets = {
    "a": colors[0],
    "b": colors[1],
    "c": colors[2],
    "d": colors[3],
    "e": colors[4],
    "f": colors[5],
    "for": None,
    "rev": "dash",
}
# %%


def invert_groups(groups):
    """
    Inverts 'group':[<substrates>] pairs in dictionary.
    :param groups: Dictionary with 'group':[<substrates>] pairs.
    :returns: Dictionary with 'substrate':'group' pairs.
    """
    inverted_groups = {}
    for group, substrates in groups.items():
        if not isinstance(substrates, list):
            substrates = [substrates]
        for substrate in substrates:
            inverted_groups[substrate] = group
    return inverted_groups


def plot_single_scan(data, visible, presets):
    traces = []
    for (pxl, dr), datum in data.groupby(["pixel", "direction"]):
        c = presets[pxl]
        d = presets[dr]
        scat = go.Scatter(
            x=datum.index.get_level_values("Voltage"),
            y=datum,
            line_color=c,
            line_dash=d,
            name=f"{pxl}\t{dr}",
            visible=visible,
            connectgaps=True,
        )
        traces.append(scat)
    return traces


def plot_single_metric(data, visible):
    traces = []
    for di, datum in data.groupby("direction"):
        pxl = datum.index.get_level_values("pixel")
        pxl = [f"pixel {px}" for px in pxl]
        box = go.Box(
            x=datum.index.get_level_values("substrate"),
            y=datum,
            boxpoints="all",
            name=di,
            hovertext=pxl,
            visible=visible,
        )
        traces.append(box)
    return traces


def plot_single_grouped_metric(data, visible, colors):
    traces = []
    for group, datum in data.groupby("group", sort=False):
        pxls = datum.index.get_level_values("pixel")
        subs = datum.index.get_level_values("substrate")
        hovertext = [f"{sub}_{pxl}" for (sub, pxl) in zip(subs, pxls)]
        color = None
        if colors is not None:
            color = colors.loc[group]
        box = go.Box(
            x=str(datum.index.get_level_values("group")),
            y=datum,
            name=group,
            marker_color=color,
            boxpoints="all",
            hovertext=hovertext,
            visible=visible,
        )
        traces.append(box)
    return traces


column_names = {
    "PCE": "PCE / %",
    "J_sc": "<i>J</i><sub>SC</sub> / mA cm<sup>&#8722;2</sup>",
    "V_oc": "<i>V</i><sub>OC</sub> / V",
    "FF": "FF / %",
    "R_ser": "<i>R</i><sub>ser</sub> / &#8486; cm<sup>2</sup>",
    "R_par": "<i>R</i><sub>par</sub> / &#8486; cm<sup>2</sup>",
}


def rename_metrics(metrics, column_names=column_names):
    metrics = metrics.rename(columns=column_names)
    return metrics


# %%
fig = bp.multilayer_plot(scans, plot_single_scan, presets=presets)
fig.update_layout(
    xaxis_title="Voltage / V",
    yaxis_title="Current density / mA cm<sup>&#8722;2</sup>",
)
# fig.add_hline(y=0)
# fig.add_vline(x=0)
# fig.show()
bt.export_asset(
    "JV-scans_plot.html",
    db,
    bp.export_plotly,
    fig,
)
# %%
metrics = ppdp.import_formatted_data(db, {"type": "raw_JV_metrics"})
metrics = metrics.drop(["J_MPP", "V_MPP"], axis=1)

# make PCE the first row (to show first in plots)
cols = metrics.columns.to_list()
cols.remove("PCE")
cols.insert(0, "PCE")
metrics = metrics[cols]

metrics.head()

# %%
plot_metrics = rename_metrics(metrics)
fig2 = bp.multilayer_plot(plot_metrics, plot_single_metric)
fig2.update_layout(
    boxmode="group"  # group together boxes of the different traces for each value of x
)
# fig.show()
# %%
bt.export_asset(
    "substrate_boxplot.html",
    db,
    bp.export_plotly,
    fig2,
)


# %%
def get_group(substrate, inverted_groups):
    if substrate in inverted_groups:
        return inverted_groups[substrate]
    else:
        return np.nan


inverted_groups = None
groups_meta = None
substrate_meta = db.find_asset(search={"type": "substrate_meta"})
if substrate_meta:
    df = pd.read_pickle(substrate_meta.file)
    try:
        df = df.loc[("general", "group")]
    except KeyError:
        pass

    inverted_groups = df.to_dict()
    groups_meta = db.find_asset(search={"type": "groups_meta"})
    if groups_meta:
        groups_meta = pd.read_pickle(groups_meta.file)
        ordering = list(groups_meta.index.values)
    else:
        df = df.sort_index()
        ordering = list(df.unique())
if ("groups" in container.metadata) and (not inverted_groups):
    groups = container.metadata["groups"]
    inverted_groups = invert_groups(groups)
    ordering = []
    for key, _ in groups.items():
        ordering.append(key)

if inverted_groups:
    metrics["group"] = [
        get_group(substrate, inverted_groups)
        for substrate in metrics.index.get_level_values("substrate")
    ]
    metrics["ordering"] = [
        np.nan if pd.isnull(group) or group not in ordering else ordering.index(group)
        for group in metrics["group"]
    ]

else:
    metrics["group"] = metrics.index.get_level_values("substrate")
# %%
metrics = metrics.set_index("group", append=True)
metrics.head()
# %%
mean = metrics.droplevel("date")
# manually remove pixels
if "drop" in container.metadata:
    drop = container.metadata["drop"]
    drop = [tuple(d.split("_")) for d in drop]
    mean = mean.drop(index=drop)
mean = mean.unstack(["pixel", "direction"])
mean = mean.stack(0)
mean = bsf.flatten_column_index(mean)
mean.columns.name = "pixel"
mean = mean.unstack(-1)
mean = mean.stack("pixel")
mean.head()
# %%
if "ordering" in mean.columns:
    mean = mean.set_index("ordering", append=True)
    mean = mean.sort_index(level="ordering")
    mean = mean.droplevel("ordering")
# %%
# hide points with V_oc < 0.2 V
mean = mean.where(lambda x: x["V_oc"] > 0.2).dropna()
mean.head()
# %%
renamed_mean = rename_metrics(mean)
colors = groups_meta["color"] if (groups_meta is not None) else None
fig3 = bp.multilayer_plot(renamed_mean, plot_single_grouped_metric, colors=colors)
fig3.update_layout(legend=dict(yanchor="top", y=1, xanchor="left", x=1.03, title=None))
_ = bt.export_asset(
    "grouped_boxplot.html",
    db,
    bp.export_plotly,
    fig3,
)

# %%

fig4 = make_subplots(2, 2, shared_xaxes=True, vertical_spacing=0, horizontal_spacing=0)


def add_facet(fig, df, df_column, column_names, colors, row, col, mirror_y=False):
    fig.add_traces(
        plot_single_grouped_metric(df[df_column], visible=True, colors=colors), row, col
    )
    fig.update_yaxes(title_text=column_names[df_column], row=row, col=col)
    if mirror_y:
        fig.update_yaxes(side="right", row=row, col=col)


add_facet(fig4, mean, "PCE", column_names, colors, 1, 1)
add_facet(fig4, mean, "J_sc", column_names, colors, 1, 2, mirror_y=True)
add_facet(fig4, mean, "FF", column_names, colors, 2, 1)
add_facet(fig4, mean, "V_oc", column_names, colors, 2, 2, mirror_y=True)
fig4.update_layout(showlegend=False)
_ = bt.export_asset(
    "faceted_grouped_boxplot.html",
    db,
    bp.export_plotly,
    fig4,
)
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
