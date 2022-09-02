# %%
import time
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries import plotly as bp
import numpy as np
import pandas as pd
# %%


def import_file(file):
    skiprows = list(range(1, 19))
    skiprows.remove(8)
    df = pd.read_csv(
        file,
        sep='\t',
        skiprows=skiprows,
        index_col=0,
        encoding='mbcs',
    )
    delay_time = df.loc['Delay Time (s)'].median()
    column_number = len(df.columns)
    columns = np.linspace(0,  delay_time * column_number-1, column_number)
    df = df.drop('Delay Time (s)')
    df.columns = pd.Index(columns, name='time/s')
    df.index = pd.Index(
        df.index.values, name='wavelength/nm', dtype=np.float32)
    return df


db = bt.init_thot(__file__)
df = ppdp.import_raw_data(
    db,
    import_file,
    sort_columns=False,
    rename_axis=False)
df.head()

bt.export_asset('continuous-PL_df.pkl', db, pd.to_pickle, df)
# %%
plot_df = df.stack('time/s')
plot_df = plot_df.droplevel('date', axis=1)
fig = bp.heatmap_3D_plot(plot_df, xaxis='wavelength/nm')
bt.export_asset('continuous-PL_plot.html', db, bp.export_plotly, fig)
