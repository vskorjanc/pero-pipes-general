# %%
from plotly import graph_objects as go
import numpy as np
import pandas as pd
from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
# %%


def read_file(file, skiprows=None, nrows=None):
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


def append_delay_time(df, delay_time):
    column_number = len(df.columns)
    columns = np.linspace(0,  delay_time * column_number-1, column_number)
    df.columns = pd.Index(columns, name='time/s')
    return df


def import_file(file):
    df = read_file(file, range(1, 19))
    delay_time = get_delay_time(file)
    df = append_delay_time(df, delay_time)
    df.index.name = 'wavelength/nm'
    # df.index = pd.Index(
    # df.index.values, name='wavelength/nm', dtype=np.float32)
    return df


def import_metrics(file):
    df = read_file(file, nrows=10)
    delay_time = get_delay_time(file)
    df = append_delay_time(df, delay_time)
    df.index.name = 'metric'
    return df


def plot_single_metric(data, visible):
    traces = []
    for su, datum in data.groupby('substrate'):
        scat = go.Scatter(
            x=datum.index.get_level_values('time/s'),
            y=datum,
            name=su,
            # hovertext=pxl,
            visible=visible,
            # mode = 'markers'
        )
        traces.append(scat)
    return traces


# %%

db = bt.init_thot(__file__)
df = ppdp.import_raw_data(
    db,
    import_file,
    sort_columns=False,
    rename_axis=False)
df.head()

# %%
metrics = ppdp.import_raw_data(
    db,
    import_metrics,
    sort_columns=False,
    rename_axis=False
)
metrics = metrics.loc[['LuQY (%)', 'iVoc (V)', 'Bandgap (eV) ']]
metrics = metrics.replace(0, np.NaN)
metrics.head()
# %%
bt.export_asset('continuous-PL_df.pkl', db, pd.to_pickle, df)
bt.export_asset('continuous-PL_metrics_df.pkl', db, pd.to_pickle, metrics)

# %%
plot_df = df.stack('time/s')
plot_df = plot_df.droplevel('date', axis=1)
# flatten in case there is pixel number
plot_df = bsf.flatten_column_index(plot_df)
fig = bp.heatmap_3D_plot(plot_df, xaxis='wavelength/nm')
bt.export_asset('continuous-PL_plot.html', db, bp.export_plotly, fig)


# %%
plot_metrics = metrics.droplevel('date', axis=1).T
metric_fig = bp.multilayer_plot(plot_metrics, plot_single_metric)
metric_fig.update_xaxes(title='time / s')
metric_fig.update_traces(connectgaps=True)
bt.export_asset('continuous-PL_metrics_plot.html',
                db, bp.export_plotly, metric_fig)
