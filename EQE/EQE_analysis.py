# %% [markdown]
# # EQE analysis

# %%
import pandas as pd
from thot import ThotProject
import numpy as np
import scipy.constants as phys
from scipy.integrate import simpson

from plotly import express as px

from bric_analysis_libraries import standard_functions as std
from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries.eqe import eqe_analysis as bea

# %% [markdown]
# ## Import AM1.5G spectrum

# %%
am = pd.read_pickle('reference_spectra/AM1.5G.pkl')
am.head()

# %% [markdown]
# ## Import measured data

# %%
thot = ThotProject(dev_root='../../../evap_pero/data/2021-11-16/EQE')
asset = thot.find_asset({'type': 'EQE_df'})

# %%
df = pd.read_pickle(asset.file)
df = df.droplevel('param', axis=1)
df.head()

# %%
int_df = bsf.interpolate(df, 0.001, 'cubic')
int_df.head()

# %%
bandgap = int_df.diff().idxmax()
metrics = pd.DataFrame(bandgap, columns=['bandgap_EQE/eV'])

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
for name, data in int_df.groupby(int_df.columns, axis=1):
    (data, fit) = bea.fit_urbach_tail(data, fit_window=0.025, filter_window=100)
    u_df.append(data)
    fits.append(fit)
u_df = pd.concat(u_df, axis=1)
fits = pd.concat(fits)
metrics['E_Urbach/eV'] = fits['e_u', 'value']

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
j0 = j0_df.apply(lambda x: simpson(x, x.index)) * phys.e
metrics['J0/(A m-2)'] = j0

# %%
[jsc_df, am_ri] = std.common_reindex([u_df, am], fillna=np.nan)
jsc_df = jsc_df.apply(
    lambda x: x * am_ri['AM1.5G/(photons s-1 m-2 eV-1)']).dropna()
jsc = jsc_df.apply(lambda x: simpson(x, x.index)) * phys.e
metrics['Jsc/(mA cm-2)'] = jsc / 10

# %%
ratio = jsc / j0
metrics['Voc_rad/V'] = ratio.apply(bea.calc_voc_rad)
metrics.head()

# %%
props = {
    'file': 'EQE_metrics.pkl',
    'type': 'EQE_metrics',
    'tags': ['EQE', 'metrics']
}
asset_path = thot.add_asset(props, 'EQE_metrics')
pd.to_pickle(metrics, asset_path)
fits.to_csv(bsf.change_extension(asset_path, 'csv'))

# %% [markdown]
# ## Plots

# %%
mpl = u_df.max()
jsc_plot = mpl * jsc_df / jsc_df.max()
j0_plot = mpl * j0_df / j0_df.max()
plot_df = pd.concat(
    [u_df, j0_plot, jsc_plot],
    keys=['interpol. EQE w/ U. tail fit',
          'J<sub>0</sub> curve', 'J<sub>SC</sub> curve'],
    axis=0,
    names=['type', 'energy']
)
plot_df.head()

# %%
for name, data in plot_df.groupby(['substrate', 'pixel'], axis=1):

    title = '_'.join(name)

    x = data.index.get_level_values('energy')
    color = data.index.get_level_values('type')
    data.columns = pd.Index(['y'])  # clearing index for Plotly to work

    fig = px.line(
        data,
        x=x,
        y='y',
        color=color,
        labels={
            'x': 'energy / eV',
            'y': 'EQE',
            'color': 'type',
        },
        title=title
    )

    measured = df[name]
    m_val = measured.values
    fig.add_scatter(x=measured.index, y=m_val, mode="markers",
                    name="measured", marker=dict(color='#FFA15A'))

    props = {
        'file': f'EQE_plot_{title}.html',
        'type': 'EQE_plot',
        'tags': ['EQE', 'plot']
    }
    asset_path = thot.add_asset(props, f'EQE_plot_{title}')
    fig.write_html(asset_path, include_plotlyjs='cdn')
