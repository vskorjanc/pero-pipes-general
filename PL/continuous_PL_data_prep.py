# %%
import numpy as np
import pandas as pd
from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
# %%


def read_file(file, skiprows, nrows=None):
    df = pd.read_csv(
        file,
        sep='\t',
        nrows=nrows,
        skiprows=skiprows,
        index_col=0,
        encoding='mbcs'
    )
    return df


def get_delay_time(file):
    delay_time = read_file(file, range(1, 8), 1)
    return delay_time.loc['Delay Time (s)'].median()


def import_file(file):
    df = read_file(file, range(1, 19))
    delay_time = get_delay_time(file)
    column_number = len(df.columns)
    columns = np.linspace(0,  delay_time * column_number-1, column_number)
    df.columns = pd.Index(columns, name='time/s')
    df.index.name = 'wavelength/nm'
    # df.index = pd.Index(
    # df.index.values, name='wavelength/nm', dtype=np.float32)
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
# flatten in case there is pixel number
plot_df = bsf.flatten_column_index(plot_df)
fig = bp.heatmap_3D_plot(plot_df, xaxis='wavelength/nm')
bt.export_asset('continuous-PL_plot.html', db, bp.export_plotly, fig)
