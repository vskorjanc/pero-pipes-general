# %%
import pandas as pd
import numpy as np
from plotly import express as px
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries import plotly as bp


# %%
def import_file(path):
    df = pd.read_csv(path, skiprows=8, header=None, encoding="latin-1", delimiter="\t")
    bin_duration = float(df.iloc[0, 0])
    df = df.iloc[2:, 0].astype(float)
    num = len(df)
    stop = num * bin_duration
    df.index = np.linspace(start=0, stop=stop, num=num, endpoint=False)
    df.index.name = "time / ns"
    return df


db = bt.init_thot(__file__)
df = ppdp.import_raw_data(db, import_file, extension=".dat", pattern="M\d-(.*?)_")
df = df.droplevel("param", axis=1)
df = df.mask(lambda x: x == 0)
df = df.dropna(how="all")
df.tail()
# %%

fig = px.line(df.loc[:1000], log_y=True)
fig.update_layout(yaxis_title="counts / s")
bt.export_asset("tr-PL_plot.html", db, bp.export_plotly, fig)

# %%
# diff_df = df.loc[150:1000]
# diff_df = diff_df.rolling(15).median()
# diff_df = diff_df.rolling(15).mean()
# diff_df = bsf.apply_savgol(diff_df, polyorder = 3, window_length=15, deriv=1)
# diff_df = diff_df.diff()
