# %%
import sys

from plotly import graph_objects as go
from plotly import express as px

from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries import thot as bt


# %%
def plot_single(data, visible):
    traces = []
    for param, datum in data.groupby("param"):
        scat = go.Scatter(
            x=datum.index.get_level_values("energy/eV"),
            y=datum,
            name=param,
            visible=visible,
        )
        traces.append(scat)
    return traces


# %%
db = bt.init_thot(__file__)

# %%
df = ppdp.import_formatted_data(db, {"type": "UV-VIS_df"})
df.columns = df.columns.droplevel(["date"])
df = df.stack("substrate", future_stack=True)
df.head()

# %%
plot_df = df.reset_index("substrate")
fig1 = px.line(plot_df, color="substrate")
fig1.update_layout(legend=dict(yanchor="top", y=1, xanchor="right", x=0.99, title=None))
_ = bt.export_asset("UV-Vis_plot.html", db, bp.export_plotly, fig1, rename=True)
# fig1.show()

# %%
if ("reflectance" or "transmittance") not in df.columns:
    sys.exit()


df["1-R"] = 1 - df["reflectance"]
df["1-R-T"] = df["1-R"] - df["transmittance"]
df = df.drop(["reflectance", "transmittance"], axis=1)
df = df.stack("param")
df = df.unstack("substrate")
df.head()

# %%
fig2 = bp.multilayer_plot(df, plot_single)
_ = bt.export_asset("R-T_plot.html", db, bp.export_plotly, fig2)
# fig2.show()
