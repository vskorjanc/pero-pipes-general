# %%
import pandas as pd
from scipy.stats import median_abs_deviation
from plotly import graph_objects as go
from bix_analysis_libraries import thot as bt, plotly as bp
from plotly import express as px
from bix_analysis_libraries.pero_pipes import data_prep as ppdp

# %%


def downsample_df(df, number_of_samples, grouping_level, other_levels):

    time_array = df.index.get_level_values(grouping_level)
    max_time = max(time_array)
    bin_size = max_time / number_of_samples

    downsampled_df = df.reset_index(grouping_level)
    # Create a new column that will be used as a grouping label
    downsampled_df["group"] = time_array // bin_size
    downsampled_df = downsampled_df.set_index("group", append=True)
    # Group by the new 'group' column and calculate the mean
    downsampled_df = downsampled_df.groupby([*other_levels, "group"]).mean()
    downsampled_df = downsampled_df.set_index(grouping_level, append=True)
    downsampled_df = downsampled_df.reset_index("group", drop=True)
    return downsampled_df


def rename_columns(df):
    df = df.rename(
        columns={
            "power / (mW cm-2)": "<i>P</i> / mW cm<sup>&#8722;2</sup>",
            "current_density / (mA cm-2)": "<i>J</i> / mA cm<sup>&#8722;2</sup>",
            "voltage / V": "<i>V</i> / V",
        }
    )
    return df


def define_property(data, level, property_values):
    """
    Defines unique property from the list of property_values
    for samples taken from index 'level' of data.
    :param data: Pandas DataFrame.
    :param level: Index level in Pandas DataFrame.
    :param property_values: List of values that are uniquely
    assigned to the samples.
    :returns: Dictionary with sample, property_value pairs.
    """
    samples = set(data.index.get_level_values(level))
    value_pairs = {}
    for nr, sample in enumerate(samples):
        indx = nr % len(property_values)
        value_pairs[sample] = property_values[indx]
    return value_pairs


# dashes = ["solid", "dot", "dash", "longdash", "dashdot", "longdashdot"]


def plot_MPP(data, visible):
    sub_c = define_property(data, "substrate", px.colors.qualitative.Plotly)
    traces = []
    for sub, pxl_datum in data.groupby("substrate"):
        c = sub_c[sub]
        if "pixel" in data.index.names:
            # pxl_d = define_property(pxl_datum, "pixel", dashes)
            for pxl, datum in pxl_datum.groupby("pixel"):
                # d = pxl_d[pxl]
                scat = go.Scatter(
                    x=datum.index.get_level_values(-1),
                    y=datum,
                    # mode="markers",
                    line_color=c,
                    # line_dash=d,
                    name=f"{sub}_{pxl}",
                    hovertext=f"{sub}_{pxl}",
                    visible=visible,
                )
                traces.append(scat)
        else:
            scat = go.Scatter(
                x=pxl_datum.index.get_level_values(-1),
                y=pxl_datum,
                # mode="markers",
                line_color=c,
                name=sub,
                hovertext=sub,
                visible=visible,
            )
            traces.append(scat)
    return traces


def hex_to_rgb(hex_string):
    hex_string = hex_string.lstrip("#")
    return tuple(int(hex_string[i : i + 2], 16) for i in (0, 2, 4))


def make_traces_with_bands(df, group, color):
    color = hex_to_rgb(color)
    x = df.index.values
    y = df["median", group]
    dy = df["mad", group]
    rgba_color = (*color, 0.3)
    traces = [
        go.Scatter(
            name=group,
            x=x,
            y=y,
            mode="lines",
            line=dict(color=f"rgb{color}"),
        ),
        go.Scatter(
            name="Upper Bound",
            x=x,
            y=y + dy,
            mode="lines",
            marker=dict(color="#444"),
            line=dict(width=0),
            showlegend=False,
        ),
        go.Scatter(
            name="Lower Bound",
            x=x,
            y=y - dy,
            line=dict(width=0),
            mode="lines",
            marker=dict(color="#444"),
            fillcolor=f"rgba{rgba_color}",
            fill="tonexty",
            showlegend=False,
        ),
    ]
    return traces


# %%
db = bt.init_thot(__file__)
df = ppdp.import_formatted_data(db, {"type": "MPP_df"})
df.head()

# %%
number_of_samples = 100
window_size = int(len(df) / number_of_samples / 10)
smooth_df = df.rolling(window_size, min_periods=1, center=True).median()
levels = ["substrate", "pixel"] if "pixel" in df.columns.names else ["substrate"]
# %%
plot_df = df.droplevel(
    "date",
    axis=1,
)

max_time = plot_df.index.max()
time = "time / s"
if max_time > 7200:
    plot_df.index = plot_df.index.map(lambda x: x / 3600)
    time = "time / h"
    plot_df.index.name = time

elif max_time > 120:
    plot_df.index = plot_df.index.map(lambda x: x / 60)
    time = "time / min"
    plot_df.index.name = time

if len(plot_df.iloc[:, 0].dropna()) > 300:
    plot_df = plot_df.stack(levels, future_stack=True)
    plot_df = downsample_df(plot_df, 100, time, levels)

plot_df.head()

# %%
mpp_plot = bp.multilayer_plot(plot_df, plot_MPP)
mpp_plot.update_layout(
    xaxis_title=time,
)
mpp_plot.update_traces(connectgaps=True)
bt.export_asset("MPP_plot.html", db, bp.export_plotly, mpp_plot, rename=True)
# mpp_plot.show()

# %%
from bix_analysis_libraries.pero_pipes import data_prep as ppdp

substrate_meta = ppdp.import_formatted_data(db, {"type": "substrate_meta"})
groups_meta = ppdp.import_formatted_data(db, {"type": "groups_meta"})
groups_meta
# %%
groups = substrate_meta.loc[("general", "group")]
ordering = list(groups_meta.index.values)
ordering = sorted(ordering)
groups = groups.to_dict()
groups
# %%
calc_df = plot_df.copy()
mad_df = pd.DataFrame()
calc_df["group"] = [
    groups[substrate] for substrate in calc_df.index.get_level_values("substrate")
]
calc_df = calc_df.set_index("group", append=True)
calc_df = calc_df["power / (mW cm-2)"]
calc_df = calc_df.unstack(["group", time])
# %%
mad_df["median"] = calc_df.median()
mad_df["mad"] = calc_df.apply(lambda x: median_abs_deviation(x, nan_policy="omit"))
mad_df = mad_df.dropna()
mad_df = mad_df.unstack("group")
mad_df
# %%
traces = []
groups = mad_df.columns.get_level_values("group").unique()
for group in groups:
    color = groups_meta.loc[group].values[0]
    traces = traces + make_traces_with_bands(mad_df, group, color)
mad_fig = go.Figure(traces)
mad_fig.update_traces(connectgaps=True)
mad_fig.update_layout(
    xaxis_title="time / h",
    yaxis_title="PCE / %",
    yaxis_range=[0, None],
    xaxis_range=[0, None],
    legend=dict(yanchor="bottom", y=0.01, xanchor="left", x=0.01, title=None),
)
# mad_fig.show()
# %%
bt.export_asset("grouped_MPP_plot_with_MAD.html", db, bp.export_plotly, mad_fig)
