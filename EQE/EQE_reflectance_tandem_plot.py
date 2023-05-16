# %%
import pandas as pd
from plotly import express as px
from plotly import graph_objects as go

from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries import plotly as bp


# %%
def plot_single(data, visible):
    colors = px.colors.qualitative.Plotly
    presets = {"Bottom": colors[0], "Top": colors[1], "1 - R": colors[2]}
    traces = []
    for pxl, data in data.groupby("param"):
        color = presets[pxl]
        line = go.Scatter(
            x=data.index.get_level_values("wavelength / nm"),
            y=data,
            line_color=color,
            name=pxl,
            visible=visible,
        )
        traces.append(line)
    return traces


# %%
db = bt.init_thot(__file__)
reflectance = ppdp.import_formatted_data(db, {"type": "reflection_tandem_df"})
reflectance = reflectance.apply(lambda x: 1 - x)
reflectance = reflectance.rename(columns={"reflectance": "1 - R"}, level="param")
reflectance.head()
# %%
eqe = ppdp.import_formatted_data(db, {"type": "EQE_tandem_df"})
eqe.head()
# %%
df = pd.concat([reflectance, eqe], axis=1, sort=True)
df.head()
# %%
plot_df = df.stack("param")
fig = bp.multilayer_plot(plot_df, plot_single)
fig.update_layout(
    xaxis_title="wavelength / nm",
)
_ = bt.export_asset("EQE_reflectance_plot.html", db, bp.export_plotly, fig)
fig.show()
# %%

presets = {"1 - R": None, "Top": "dash", "Bottom": "dot"}

fig2 = go.Figure()
color_count = 0
for sub, data in plot_df.groupby("substrate", axis=1):
    (color, color_count) = bp.give_next_color(color_count)
    for param, datum in data.groupby("param"):
        y = datum[sub].values
        x = datum.index.get_level_values("wavelength / nm")
        showlegend = True if param == "1 - R" else False
        dash = presets[param]
        fig2.add_trace(
            go.Scatter(
                y=y,
                x=x,
                line_dash=dash,
                line_color=color,
                legendgroup=sub,
                name=sub,
                showlegend=showlegend,
            )
        )
fig2.update_layout(
    xaxis_title="wavelength / nm",
    legend_title="Substrate",
)
_ = bt.export_asset("EQE_reflectance_plot_all.html", db, bp.export_plotly, fig)
fig2.show()
