# %%
from plotly import express as px
from plotly import graph_objects as go
from bix_analysis_libraries import (
    thot as bt,
    plotly as bp,
    bix_standard_functions as bsf,
)
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
import pandas as pd

# %%


def import_file(file):
    df = pd.read_csv(
        file,
        sep="\t",
        names=["wavelength / nm", "SR / A W-1", "EQE", "uncertainty"],
        skiprows=1,
        index_col="wavelength / nm",
        usecols=["wavelength / nm", "EQE"],
        engine="python",
        skipfooter=17,
        encoding="ISO-8859-15",
    )
    return df


def plot_single(data, visible):
    colors = px.colors.qualitative.Plotly
    presets = {"Bottom": colors[0], "Top": colors[1]}
    traces = []
    for pxl, data in data.groupby("subcell"):
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
df = ppdp.import_raw_data(
    db,
    import_file,
    has_date=False,
    pattern="ID (.+?)(?:-\d)? cell (?:\d{2})?_Tandem (Top|Bottom).+",
)
df = df.droplevel("param", axis=1)
df = df.sort_index()
df.columns = df.columns.rename({"pixel": "subcell"})
df.head()

# %%
_ = bt.export_asset("EQE_tandem_df.pkl", db, bsf.export_pickle, df)
# %%
plot_df = df.stack("subcell", future_stack=True)
fig = bp.multilayer_plot(plot_df, plot_single)
fig.update_layout(xaxis_title="wavelength / nm", yaxis_title="EQE")
_ = bt.export_asset("EQE_tandem_plot.html", db, bp.export_plotly, fig)
