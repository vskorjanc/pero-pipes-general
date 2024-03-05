# %%
from plotly import express as px

from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries import bix_standard_functions as bsf


# %%
def plot_df(df):
    plot_df = df.copy()
    plot_df = plot_df.reset_index("substrate")
    fig = px.line(plot_df, y="1-R-T", color="substrate")
    fig.update_xaxes(range=[1.515, 2.154])
    return fig


# %%
db = bt.init_thot(__file__)
df = ppdp.import_formatted_data(db, {"type": "UV-VIS_df"})
df = df.sort_index()
df = df.iloc[300:]
df = df.droplevel("date", axis=1)
df = bsf.interpolate(df, 0.001, "cubic")
df = df.stack("substrate")
df["1-R"] = 1 - df["reflectance"]
df["1-R-T"] = df["1-R"] - df["transmittance"]
df.head()
# %%
fig = plot_df(df)
fig.show()
# %%
diff_df = df.unstack("substrate")
diff_df = bsf.apply_savgol(diff_df, window_length=241, deriv=1)
diff_df = diff_df.stack("substrate")
diff_fig = plot_df(diff_df)
diff_fig.show()
# %%
bt.export_asset("UV-VIS_diff_plot.html", db, bp.export_plotly, diff_fig)
