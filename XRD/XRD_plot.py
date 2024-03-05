# %%
from plotly import express as px
from plotly import graph_objects as go
from plotly.subplots import make_subplots

from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp

# %%
db = bt.init_thot(__file__)
df = ppdp.import_formatted_data(db, {"type": "XRD_df"})
df = df.droplevel(["date", "param"], axis=1)
df.head()
# %%
idx = df.index.values
min_max = (idx.min(), idx.max())
# %%
compounds = bt.import_global_asset(
    db=db,
    a_type="XRD_pattern_df",
    a_path="../../../../scripts/common/XRD/patterns/patterns.pkl",
    dev_path="patterns/patterns.pkl",
)
compounds = compounds.droplevel(-1, axis=1)
compounds = compounds[compounds.index >= min_max[0]]
compounds = compounds[compounds.index <= min_max[1]]
compounds.head()
# %%
fig1 = px.line(df)
fig1.update_layout(
    xaxis_title="2<i>&#920;</i> / &deg;",
    yaxis={
        "title": "intensity",
        "showticklabels": False,
        "showgrid": False,
        "ticks": "",
    },
    legend_title=None,
)
_ = bt.export_asset("XRD_plot.html", db, bp.export_plotly, fig1)
# %%
stacked_df = df.copy()
spacing = (len(stacked_df.columns)) * 1.05
print(spacing)
for column in stacked_df:
    stacked_df[column] += spacing
    spacing -= 1.1
stacked_fig = px.line(stacked_df)
stacked_fig.update_layout(
    xaxis_title="2<i>&#920;</i> / &deg;",
    yaxis={
        "title": "intensity",
        "showticklabels": False,
        "showgrid": False,
        "ticks": "",
    },
    legend={"title": None, "xanchor": "right", "x": 0.99},
)
# stacked_fig.show()
_ = bt.export_asset("XRD_stacked_plot.html", db, bp.export_plotly, stacked_fig)
# %%


def add_subplot(df, fig, name, row, visible=None):
    for column in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index.values,
                y=df[column],
                name=column,
                visible=visible,
                legendgroup=name,
                legendgrouptitle_text=name,
            ),
            row=row,
            col=1,
        )


fig2 = make_subplots(rows=2, shared_xaxes=True, vertical_spacing=0)
add_subplot(df, fig2, "Substrate", 1)
add_subplot(compounds, fig2, "Compound", 2, visible="legendonly")

fig2.update_xaxes(title="2<i>&#920;</i> / &deg;", row=2, col=1)
fig2.update_yaxes(showticklabels=False, showgrid=False, ticks="")
fig2.update_layout(
    legend=dict(xanchor="left", yanchor="top", x=1.01, y=1, groupclick="toggleitem")
)
bt.export_asset("XRD_comparison_plot.html", db, bp.export_plotly, fig2)
# fig.show()
