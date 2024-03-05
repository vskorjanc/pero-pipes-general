# %%
from scipy.stats import linregress
import pandas as pd
import numpy as np
from plotly import express as px
import scipy.constants as phys

from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries import bix_standard_functions as bsf

# %%
db = bt.init_thot(__file__)
metrics = ppdp.import_formatted_data(db, {"type": "JV_metrics"})
names = metrics.index.get_level_values("substrate")
substrates = []
intensities = []
for name in names:
    split_name = name.split("_")
    substrate = split_name[0]
    substrates.append(substrate)
    intensity = int(split_name[1])
    intensities.append(intensity)


metrics = metrics.set_index(
    [substrates, intensities],
    append=True,
)
metrics = metrics.droplevel("substrate")
metrics.index.names = ["pixel", "substrate", "intensity"]
metrics["intensity / sun"] = [i / 100 for i in intensities]
metrics["ln(intensity)"] = [np.log(i) for i in intensities]
metrics = metrics.sort_index(level="substrate")
metrics


# %%
plot_df = metrics.copy()
plot_df.columns.name = "param"
plot_df = plot_df.unstack(["substrate", "pixel"])
plot_df = plot_df.stack("param")
plot_df = bsf.flatten_column_index(plot_df)
plot_df.columns.name = "pixel"
plot_df = plot_df.unstack("param")
plot_df = plot_df.stack("pixel")


# %%
def plot_param(param, plot_df, db, log_y=False):
    fig = px.line(
        plot_df,
        x="intensity / sun",
        y=param,
        log_x=True,
        log_y=log_y,
        color=plot_df.index.get_level_values("pixel"),
        # line_dash=plot_df.index.get_level_values("pixel"),
        markers=True,
    )
    yaxis_names = {
        "PCE": "PCE / %",
        "J_sc": "<i>J</i><sub>SC</sub> / mA cm<sup>&#8722;2</sup>",
        "V_oc": "<i>V</i><sub>OC</sub> / V",
        "FF": "FF / %",
        "R_ser": "<i>R</i><sub>ser</sub> / &#8486; cm<sup>2</sup>",
        "R_par": "<i>R</i><sub>par</sub> / &#8486; cm<sup>2</sup>",
    }
    fig.update_layout(yaxis_title=yaxis_names[param], legend_title=None)

    _ = bt.export_asset(f"{param}_intensity_plot.html", db, bp.export_plotly, fig)
    return fig


Voc_fig = plot_param("V_oc", plot_df, db)
Jsc_fig = plot_param("J_sc", plot_df, db, log_y=True)
FF_fig = plot_param("FF", plot_df, db)


# %%
def fit_lin(data):
    fit = linregress(data["ln(intensity)"], data["V_oc"])
    kb = phys.physical_constants["Boltzmann constant"][0]
    e = phys.physical_constants["elementary charge"][0]
    t = 298
    n = fit.slope * e / kb / t
    r_squared = fit.rvalue**2
    return pd.DataFrame([[n, r_squared]], columns=["ideality factor", "r squared"])


fit_df = metrics.groupby(["substrate", "pixel"]).apply(fit_lin)
fit_df = fit_df.droplevel(-1)
fit_df.head()
ppdp.pickle_w_markdown(fit_df, "ideality_factor_fit", db, floatfmt=".2f")
