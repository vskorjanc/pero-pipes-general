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

# %% [markdown]
# ## Import measured data

# %%
db = bt.init_thot(__file__)

# %%
df = ppdp.import_formatted_data(db, {"type": "EQE_df"})
df = df.droplevel("param", axis=1)
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

# %%
int_df = bsf.interpolate(df, 0.001, "cubic")
int_df.head()

# %%
bandgap = int_df.diff().idxmax()
metrics = pd.DataFrame(bandgap, columns=["bandgap_EQE/eV"])

# %% [markdown]
# ## Urbach tail fit
# To avoid background noise from influencing the $J_0,rad$ determination, the part of the spectrum up to the inflection point (in the log scale) is fitted with an Urbach tail:
# $$
# \alpha \left (E \right ) = \alpha_0 \exp{\left ( \frac{E - E_\mathrm{C}}{E_\mathrm{U}} \right )}
# $$
# $$
# \ln{\alpha \left (E \right )} = \frac{1}{E_\mathrm{U}} E + \left ( \ln{\alpha_0} - \frac{E_\mathrm{C}}{E_U} \right )
# $$
# [Source](https://doi.org/10.1021/acs.jpclett.9b00138)
#

# %%
u_df = []
fits = []
for name, data in int_df.T.groupby(int_df.columns):
    data = data.copy().T
    (data, fit) = bea.fit_urbach_tail(data, fit_window=0.025, filter_window=100)
    u_df.append(data)
    fits.append(fit)
u_df = pd.concat(u_df, axis=1)
fits = pd.concat(fits)
metrics["E_Urbach/eV"] = fits["e_u", "value"]

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
j0_df = u_df.apply(bea.calc_bb)
j0 = j0_df.apply(lambda x: simpson(y=x, x=x.index)) * phys.e
metrics["J0/(A m-2)"] = j0

# %%
jsc = bea.calc_Jsc(u_df, am)
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
mpl = u_df.max()
# jsc_plot = mpl * jsc_df / jsc_df.max()
j0_plot = mpl * j0_df / j0_df.max()
plot_df = pd.concat(
    [df, u_df, j0_plot],
    keys=[
        "measured",
        "interpol. EQE w/ U. tail fit",
        "J<sub>0</sub> curve",
        # "J<sub>SC</sub> curve",
    ],
    axis=0,
    names=["type", "energy"],
)
plot_df = plot_df.droplevel("date", axis=1)
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
            name=tp,
            visible=visible,
        )
        traces.append(scat)
    return traces


fig = bp.multilayer_plot(plot_df, plot_analysis_curves)
bt.export_asset("EQE_analysis_plot.html", db, bp.export_plotly, fig)
