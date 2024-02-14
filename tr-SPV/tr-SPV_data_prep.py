# %%
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries import plotly as bp
from plotly import express as px
import pandas as pd


# %%
def import_file(path):
    df = pd.read_csv(path, sep="\t", skipfooter=55, engine="python", index_col=0)
    df.columns = df.columns.astype(float)
    return df


db = bt.init_thot(__file__)
df = ppdp.import_raw_data(db, import_file, pattern=r"(.*?)_(?=.*)", has_date=False)
df.columns = df.columns.set_names("wavelength / nm", level="param")
df.head()
# %%
plot_df = df.stack("wavelength / nm")
plot_df = plot_df.reset_index("wavelength / nm")

range_y = bsf.set_axlims(df.values)

fig = px.line(plot_df, log_x=True, animation_frame="wavelength / nm", range_y=range_y)
fig.update_layout(
    xaxis_title="time / s",
    yaxis_title="voltage / V",
)
_ = bt.export_asset("tr-SPV_line_plot.html", db, bp.export_plotly, fig)
