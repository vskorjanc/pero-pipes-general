# %%
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from plotly import graph_objects as go
from plotly import express as px

# %%
db = bt.init_thot(__file__)
df = ppdp.import_formatted_data(db, {"type": "JV_scans"})
df.head()
# %%
presets = {"forw": None, "rev": "dash"}

# %%

fig = go.Figure()
color_count = 0
for sub, data in df.groupby("substrate", axis=1):
    (color, color_count) = bp.give_next_color(color_count)
    for direction, datum in data.groupby("direction"):
        y = datum[sub].values
        x = datum.index.get_level_values("voltage")
        showlegend = False if direction == "rev" else True
        dash = presets[direction]
        fig.add_trace(
            go.Scatter(
                y=-y,
                x=-x,
                line_dash=dash,
                line_color=color,
                legendgroup=sub,
                name=sub,
                showlegend=showlegend,
            )
        )
fig.update_layout(
    xaxis_title="Voltage / V",
    yaxis_title="Current density / mA cm<sup>&#8722;2</sup>",
    legend_title="Substrate",
)
_ = bt.export_asset("tandem_JV_plot.html", db, bp.export_plotly, fig)
