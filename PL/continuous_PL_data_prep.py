# %%
from plotly import graph_objects as go
import numpy as np
import plotly.colors as pc
from plotly import express as px
import pandas as pd
from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries.pero_pipes import data_prep as ppdp

# %%


def read_file(file, skiprows=None, nrows=None):
    df = pd.read_csv(
        file,
        sep="\t",
        nrows=nrows,
        skiprows=skiprows,
        index_col=0,
        encoding="unicode_escape",
    )
    return df


def get_spacing(file):
    data = read_file(file, 0, 9)
    delay_time = data.loc["Delay Time (s)"].median()
    integration_time = data.loc["Integration Time (ms)"].median() / 1000
    if delay_time >= integration_time:
        spacing = delay_time
    else:
        spacing = integration_time
    return spacing


def append_spacing(df, spacing):
    column_number = len(df.columns)

    # columns = np.arange(column_number * spacing, spacing)
    # print(columns)
    columns = np.linspace(0, spacing * column_number - 1, column_number)

    df.columns = pd.Index(columns, name="time/s")
    return df


def import_file(file):
    if "_raw" in file:
        return pd.DataFrame()
    df = read_file(file, range(1, 19))
    spacing = get_spacing(file)
    df = append_spacing(df, spacing)
    df.index.name = "wavelength/nm"
    # df.index = pd.Index(
    # df.index.values, name='wavelength/nm', dtype=np.float32)
    return df


def import_metrics(file):
    if "_raw" in file:
        return pd.DataFrame()
    df = read_file(file, nrows=10)
    spacing = get_spacing(file)
    df = append_spacing(df, spacing)
    df.index.name = "metric"
    return df


def plot_single_metric(data, visible):
    traces = []
    for su, datum in data.groupby("substrate"):
        scat = go.Scatter(
            x=datum.index.get_level_values("time/s"),
            y=datum,
            name=su,
            # hovertext=pxl,
            visible=visible,
            # mode = 'markers'
        )
        traces.append(scat)
    return traces


db = bt.init_thot(__file__)
df = ppdp.import_raw_data(
    db, import_file, sort_columns=False, rename_axis=False, extension=".txt"
)
df.head()

# %%
metrics = ppdp.import_raw_data(
    db, import_metrics, sort_columns=False, rename_axis=False, extension=".txt"
)
metrics = metrics.loc[["LuQY (%)", "iVoc (V)", "Bandgap (eV) "]]
metrics = metrics.replace(0, np.nan)
metrics.head()
# %%
bt.export_asset("continuous-PL_df.pkl", db, pd.to_pickle, df)
bt.export_asset("continuous-PL_metrics_df.pkl", db, pd.to_pickle, metrics)

# %%
plot_df = df.stack("time/s", future_stack=True)
plot_df = plot_df.droplevel("date", axis=1)
# flatten in case there is pixel number
plot_df = bsf.flatten_column_index(plot_df)
heatmap_fig = bp.heatmap_3D_plot(plot_df, xaxis="wavelength/nm")
bt.export_asset("continuous-PL_heatmap_plot.html", db, bp.export_plotly, heatmap_fig)

# %%

colorscale = "viridis"


def generate_colors_from_colorscale(colorscale, array):
    """
    Generates a dictionary mapping array items to colors from a continuous colorscale.

    Parameters:
    colorscale: str or list of tuple
        The name of the colorscale (e.g., 'Viridis', 'Plasma') or a custom colorscale.
    array: list
        The array of items for which the colors are generated.

    Returns:
    dict
        A dictionary where keys are array items and values are color values in hex format.
    """
    colorscale = "viridis"
    colorscale = pc.get_colorscale(colorscale)

    array_length = len(array)

    # Generate evenly spaced values between 0 and 1
    values = np.linspace(0, 1, array_length)

    # Map the values to colors using the colorscale
    colors = pc.sample_colorscale(colorscale, values, colortype="rgb")

    # Create a dictionary mapping array items to colors
    color_mapping = dict(zip(array, colors))

    return color_mapping


# %%


def add_colorbar_to_figure(colorscale, visible, time_array):
    """
    Adds a colorbar to a Plotly figure based on the provided colorscale and array.

    Parameters:
    colorscale: str or list of tuple
        The colorscale to use for the colorbar.
    array: list
        The array of items to represent along the colorbar.
    figure: plotly.graph_objects.Figure
        The Plotly figure to which the colorbar will be added.

    Returns:
    plotly.graph_objects.Figure
        The updated figure with the colorbar added.
    """
    # array_length = len(array)
    # values = np.linspace(0, 1, array_length)

    # Add colorbar to the figure
    trace = go.Scatter(
        x=[None],  # Dummy data to create the colorbar
        y=[None],
        mode="markers",
        visible=visible,
        marker=dict(
            color=[0, 1],
            colorscale=colorscale,
            showscale=True,
            colorbar=dict(
                title="Time / s",
                tickvals=[0, 1],
                ticktext=[time_array.min(), time_array.max()],
            ),
        ),
        showlegend=False,
        hoverinfo="none",
    )

    return trace


def plot_single_spectrum(data, visible, color_mapping):
    traces = []
    time_array = data.index.get_level_values("time/s")
    for time, datum in data.groupby("time/s"):
        x = datum.index.get_level_values("wavelength/nm")
        y = datum
        scat = go.Scatter(
            x=x,
            y=y,
            name=time,
            marker_color=color_mapping[time],
            visible=visible,
            showlegend=False,
        )
        traces.append(scat)
    cb_trace = add_colorbar_to_figure(colorscale, visible, time_array)
    traces.append(cb_trace)

    return traces


time_array = plot_df.index.get_level_values("time/s").unique()
color_mapping = generate_colors_from_colorscale(colorscale, time_array)
spectral_fig = bp.multilayer_plot(
    plot_df, plot_single_spectrum, color_mapping=color_mapping
)
# add_colorbar_to_figure('viridis', time_array, spectral_fig)
spectral_fig.update_layout(xaxis_title="wavelength / nm", yaxis_title="intensity")
bt.export_asset("continuous-PL_spectral_plot.html", db, bp.export_plotly, spectral_fig)
# spectral_fig.show()


# %%
points_to_average = 5
average_df = {}
for wl, data in plot_df.groupby("wavelength/nm"):
    average_df[wl] = data.iloc[-points_to_average:].mean()
average_df = pd.concat(
    average_df.values(), keys=average_df.keys(), names=["wavelength/nm", "substrate"]
)
average_df = average_df.unstack("substrate")
bt.export_asset("continuous-PL_averaged_df.pkl", db, pd.to_pickle, average_df)
average_df.head()

# %%
averaged_fig = px.line(average_df)
averaged_fig.update_layout(yaxis_title="intensity")
bt.export_asset(
    "continuous-PL_averaged_plot.html",
    db,
    bp.export_plotly,
    averaged_fig,
    rename=True,
)
# %%
average_metrics = {}
for sub, data in metrics.T.groupby("substrate"):
    average_metrics[sub] = data.iloc[-points_to_average:].median()
average_metrics = pd.concat(average_metrics, axis=1, names=["substrate"]).T
ppdp.pickle_w_markdown(
    average_metrics, "continuous-PL_averaged_metrics", db, floatfmt=".2f"
)
average_metrics.head()
# %%
plot_metrics = metrics.droplevel("date", axis=1).T
metric_fig = bp.multilayer_plot(plot_metrics, plot_single_metric)
metric_fig.update_xaxes(title="time / s")
metric_fig.update_traces(connectgaps=True)
bt.export_asset("continuous-PL_metrics_plot.html", db, bp.export_plotly, metric_fig)
