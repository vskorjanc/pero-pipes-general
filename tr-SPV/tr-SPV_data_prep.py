# %%
from bix_analysis_libraries import thot as bt
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
df.head()
# %%
df_620 = df.xs(620, axis=1, level="param")
df_620.head()
# %%
fig_620 = px.line(df_620, log_x=True)
_ = bt.export_asset("tr-SPV_line_plot_620nm.html", db, bp.export_plotly, fig_620)
