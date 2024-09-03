# %% [markdown]
# # EQE analysis

# %%
import numpy as np
from scipy.optimize import curve_fit

from plotly import graph_objects as go
from pathlib import Path
import pandas as pd

import scipy.constants as phys
from scipy.integrate import simpson


from bix_analysis_libraries import (
    bix_standard_functions as bsf,
    thot as bt,
    plotly as bp,
)
from bix_analysis_libraries.eqe import eqe_analysis as bea
from bix_analysis_libraries.pero_pipes import data_prep as ppdp

# %% [markdown]
# ## Import measured data

# %%
db = bt.init_thot(__file__)

# %%
df = ppdp.import_formatted_data(db, {"type": "EQE_df"})
df = df.droplevel(["param", "date"], axis=1)
df.head()
# %% [markdown]
# ## Import AM1.5G spectrum
# %%
am = bt.import_global_asset(
    db,
    a_path=r"root:/../scripts/common/EQE/reference_spectra/AM1.5G.pkl",
    dev_path=Path(r"reference_spectra/AM1.5G.pkl"),
    a_type="AM1.5G",
    import_function=pd.read_pickle,
)

am.head()

# %% [markdown]
# ## Sigmoidal curve fit
# Due to robustness, the sigmoidal curve fit is preferred over the Urbach tail fit. The approach from the source was adjusted for calculation in the energy instead of wavelength domain.
#
# $$
# \operatorname{EQE}(E)=\frac{A_{\mathrm{m}}}{1+\exp \left[2.63\left(E-E{\mathrm{g}}\right) / E{\mathrm{s}}\right]}
# $$
# 2.63 is a numeric factor that sets the steepness to be equal to the distance between the minimum and maximum of the second derivative of the sigmoidal curve.
#
# Source: https://doi.org/10.1002/aenm.202100022

# %%


def sigmoid_function(x, amplitude, midpoint, steepness):
    return amplitude / (1 + np.exp(-2.63 * (x - midpoint) / steepness))


def fit_sigmoid(series, area_width):
    interpol_series = bsf.interpolate(series, 0.001, "cubic")
    # take inflection point as the midpoint guess
    midpoint_guess = (
        bsf.apply_savgol(interpol_series, window_length=200, deriv=1).idxmax().values[0]
    )

    amplitude_guess = series.max()
    if amplitude_guess > 1:
        amplitude_guess = 1
    steepness_guess = 0.04

    selected = series.loc[midpoint_guess - area_width : midpoint_guess + area_width]

    x_data = selected.index.values
    y_data = selected.values

    p0 = [amplitude_guess, midpoint_guess, steepness_guess]

    popt, _ = curve_fit(
        sigmoid_function, x_data, y_data, p0=p0, bounds=([0, 1.5, 0], [1, 2.2, 0.1])
    )
    return popt, midpoint_guess


# %%
fit = pd.DataFrame(
    index=pd.Index(["amplitude", "midpoint", "steepness"]), columns=df.columns
)
sigmoid_tail_df = df.copy()
sigmoid_df = pd.DataFrame(
    index=np.arange(df.index.min(), df.index.max(), 0.001), columns=df.columns
)
area_width = 0.1
for column in df.columns:
    popt, midpoint_guess = fit_sigmoid(df[column], area_width)
    fit[column] = popt
    # set the values below the inflection point to the fit values for J0 calculation
    sigmoid_tail_df.loc[: popt[1], column] = [
        sigmoid_function(x, *popt) for x in sigmoid_tail_df.loc[: popt[1]].index.values
    ]
    sigmoid_df.loc[
        midpoint_guess - area_width : midpoint_guess + area_width, column
    ] = [
        sigmoid_function(x, *popt)
        for x in sigmoid_df.loc[
            midpoint_guess - area_width : midpoint_guess + area_width
        ].index.values
    ]

sigmoid_tail_df = bsf.interpolate(sigmoid_tail_df, 0.001, "cubic")
metrics = pd.DataFrame(fit.T[["midpoint", "steepness"]])
metrics = metrics.rename({"midpoint": "bandgap/eV"}, axis=1)
metrics


# %% [markdown]
# ## Determining $V_{\mathrm{OC,rad}}$
# The radiative limit of the open circuit voltage is calculated as:
# $$
# V_{\mathrm{OC,rad}} = \frac{k_\mathrm{B} T}{q} \ln{\left (\frac {J_{\mathrm{SC}}}{J_{\mathrm{0,rad}}} \right )}
# $$
# ### Determining $J_\mathrm{0,rad}$
# $$
# J_{\mathrm{0,rad}} = q \int_{0}^{\inf}{EQE(E) \phi_{\mathrm{bb}}(E) \mathrm{~d}E}
# $$
# where $\phi_{\mathrm{bb}}(E)$ is the photon flux:
# $$
# \phi_{\mathrm{bb}}(E) = \frac{{2{\mathrm{\pi}} E^2}}{{h^3c^2}}\frac{1}{{\exp \left( \frac{E}{{k_{\mathrm{B}}T}} \right)- 1}}
# $$
#
# ### Determining $J_{\mathrm{SC}}$
# $$
# J_{\mathrm{SC}} = q \int_{0}^{\inf}{EQE(E) \phi_{\mathrm{AM1.5G}}(E) \mathrm{~d}E}
# $$
# Where $\phi_{\mathrm{AM1.5G}}(E)$ is the Air mass 1.5 global reference spectrum.
#
# [Source](https://www.nature.com/articles/srep06071)

# %%
j0_df = sigmoid_tail_df.apply(bea.calc_bb)
j0 = j0_df.apply(lambda x: simpson(y=x, x=x.index)) * phys.e
metrics["J0/(A m-2)"] = j0

# %%
jsc = bea.calc_Jsc(sigmoid_tail_df, am)
metrics["Jsc/(mA cm-2)"] = jsc

# %%
ratio = jsc / j0
metrics["Voc_rad/V"] = ratio.apply(bea.calc_voc_rad)
metrics.head()

# %%
ppdp.pickle_w_markdown(metrics, "EQE_metrics", db)

# %% [markdown]
# ## Plots

# %%
mpl = sigmoid_tail_df.max()
# jsc_plot = mpl * jsc_df / jsc_df.max()
j0_plot = mpl * j0_df / j0_df.max()
plot_df = pd.concat(
    [df, sigmoid_df, sigmoid_tail_df, j0_plot],
    keys=[
        "measured",
        "sigmoid fit",
        "interpol. EQE w/ S. tail fit",
        "J<sub>0</sub> curve",
        # "J<sub>SC</sub> curve",
    ],
    axis=0,
    names=["type", "energy"],
)
plot_df = bsf.flatten_column_index(plot_df)
plot_df.head()

# %%


def plot_analysis_curves(data, visible):
    traces = []
    for tp, datum in data.groupby("type"):
        scat = go.Scatter(
            x=datum.index.get_level_values("energy"),
            y=datum,
            mode="markers" if tp == "measured" else "lines",
            line_dash="dot" if tp == "sigmoid fit" else None,
            name=tp,
            visible=visible,
        )
        traces.append(scat)
    return traces


fig = bp.multilayer_plot(plot_df, plot_analysis_curves)
fig.update_layout(legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99))
bt.export_asset("EQE_analysis_plot.html", db, bp.export_plotly, fig)
