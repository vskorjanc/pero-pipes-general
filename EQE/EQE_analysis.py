# %% [markdown]
# # EQE analysis

# %%
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
from bric_analysis_libraries.pl import pl_data_prep as pdp

# %% [markdown]
# ## Import measured data

# %%
db = bt.init_thot(__file__)

# %%
try:
    df = ppdp.import_formatted_data(db, {"type": "EQE_df"})
    df = df.droplevel(["param", "date"], axis=1)
except SystemExit:
    df = ppdp.import_formatted_data(db, {"type": "EQE_tandem_df"})
    df = pdp.index_to_energy(df)
    df.index.name = "energy / eV"
    df = df.xs(
        "Top",
        axis=1,
        level="subcell",
        # drop_level=False
    )
    df = df.dropna(how="all")
    df = df.dropna(how="all", axis=0)
    df = df.sort_index()
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
sigmoid_df, sigmoid_tail_df, metrics = bea.apply_sigmoid_fit(df)


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
