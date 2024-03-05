# %%
from bix_analysis_libraries import thot as bt, plotly as bp
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries.pl import pl_data_prep as pldp
import pandas as pd
from plotly import express as px

# %%


def import_file(file):
    skiprows = 17
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        if "iVoc (V) HET" in f.read():
            skiprows = 18
    df = pd.read_csv(
        file,
        sep="\t",
        skiprows=skiprows,
        encoding="unicode_escape",
        index_col=0,
        names=["wavelength/nm", "flux [photons/(cm2 s nm)]", "counts/s"],
        usecols=["wavelength/nm", "flux [photons/(cm2 s nm)]"],
    )
    return df


def import_metric(file):
    metrics = [
        "LuQY (%)",
        "iVoc (V)",
        "iVoc (V) HET",
        "Bandgap (eV)",
        "Jsc (mA/cm2)",
    ]
    df = pd.read_csv(file, sep="\t", nrows=11, encoding="unicode_escape", index_col=0)
    if "iVoc (V) HET" not in df.index.values:
        metrics.remove("iVoc (V) HET")
    df = df.loc[metrics]
    return df


def import_metrics(db):
    metrics = ppdp.import_raw_data(db, import_metric)
    metrics = metrics.droplevel("date", axis=1)
    if "pixel" in metrics.columns.names:
        metrics.columns.names = ["substrate", "pixel", "date"]
    else:
        metrics.columns.names = ["substrate", "date"]
    return metrics.T


# %%
db = bt.init_thot(__file__)
metrics = import_metrics(db)
ppdp.pickle_w_markdown(metrics.droplevel("date"), "PL_metrics", db)
metrics.head()

# %%
df = ppdp.import_raw_data(db, import_file)
df = pldp.df_to_energy(df)
df = df * 10000  # convert from cm-2 to m-2
df = df.rename(
    columns={"flux [photons/(cm2 s nm)]": "flux [photons/(m2 s eV)]"}, level="param"
)
df.head()
# %%
plot_df = df.droplevel(["date"], axis=1)
# name = ['_'.join(col) for col in plot_df.columns.values]
columns = list(plot_df.columns.names)
columns.remove("param")
plot_df = plot_df.stack(columns, future_stack=True)
plot_df = plot_df.reset_index(columns)
plot_df.head()
# %%
line_dash = "pixel" if "pixel" in columns else None
fig = px.line(plot_df, color="substrate", line_dash=line_dash)
fig.update_layout(
    xaxis_title="energy / eV",
    yaxis_title="photon flux / m<sup>-2</sup> s<sup>-1</sup> eV<sup>-1</sup>",
    legend_title=None,
)
bt.export_asset("PL_plot.html", db, bp.export_plotly, fig)
# fig.show()
