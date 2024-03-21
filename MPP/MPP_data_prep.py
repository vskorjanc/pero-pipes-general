# %%
from plotly import graph_objects as go
from bix_analysis_libraries import thot as bt, plotly as bp
from plotly import express as px
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
import pandas as pd

# %%


def import_file(file):
    df = pd.read_csv(
        file,
        sep="\t",
        skiprows=8,
        names=["time/s", "voltage/V", "current_density/(mA cm-2)", "power/(mW cm-2)"],
        encoding="ISO-8859-15",
    )
    df = df.dropna()
    df = df.drop_duplicates("time/s")
    df["time/s"] = pd.to_numeric(df["time/s"])
    for column in df.columns:
        df[column] = abs(df[column])
    df = df.set_index("time/s")
    return df


def rename_columns(df):
    df = df.rename(
        columns={
            "power/(mW cm-2)": "SPO / mW cm<sup>&#8722;2</sup>",
            "current_density/(mA cm-2)": "<i>J</i> / mA cm<sup>&#8722;2</sup>",
            "voltage/V": "<i>V</i> / V",
        }
    )
    return df


# %%
db = bt.init_thot(__file__)
df = ppdp.import_raw_data(db, import_file)
df = df.sort_index()

bt.export_asset("MPP_df.pkl", db, pd.to_pickle, df)
df.head()
# %%
plot_df = df.droplevel("date", axis=1)
to_stack = list(plot_df.columns.names)
to_stack.remove("param")
plot_df = plot_df.stack(to_stack, future_stack=True)
cols = plot_df.columns.to_list()
cols.remove("power/(mW cm-2)")
cols.insert(0, "power/(mW cm-2)")
plot_df = plot_df[cols]
plot_df = rename_columns(plot_df)
plot_df.head()
# %%


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
                    x=datum.index.get_level_values("time/s"),
                    y=datum,
                    mode="markers",
                    line_color=c,
                    # line_dash=d,
                    name=f"{sub}_{pxl}",
                    visible=visible,
                )
                traces.append(scat)
        else:
            scat = go.Scatter(
                x=pxl_datum.index.get_level_values("time/s"),
                y=pxl_datum,
                mode="markers",
                line_color=c,
                name=sub,
                visible=visible,
            )
            traces.append(scat)
    return traces


# %%
fig = bp.multilayer_plot(plot_df, plot_MPP)
fig.update_layout(xaxis_title="time / s", legend={"itemsizing": "constant"})
fig.update_traces(marker_size=2)
bt.export_asset("MPP_plot.html", db, bp.export_plotly, fig)
