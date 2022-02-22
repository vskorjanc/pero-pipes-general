# %% [markdown]
# # Absolute PL calculation
#
# Calculates QFLS ($\mathrm{\Delta }E_{\mathrm{F}}$) from PL spectrum using Wurfel's generalized Planck's law:
# $$
# I_{{\mathrm{PL}}}\left( E \right) = \frac{{2{\mathrm{\pi}} E^2a\left( E \right)}}{{h^3c^2}}\frac{1}{{\exp \left( \frac{{E - \mathrm{\Delta }E_{\mathrm{F}}}}{{k_{\mathrm{B}}T}} \right)- 1}}
# $$
#
# ## Approximations
# If we assume that $\exp{\frac{{E - \mathrm{\Delta }E_{\mathrm{F}}}}{{k_{\mathrm{B}}T}}} >> 1$ and $a\left( E \right) \approx 1$, we may write:
#
# $$\ln \left( {\frac{{I_{{\mathrm{PL}}}\left( E \right)h^3c^2}}{{2{\mathrm{\pi}} E^2}}} \right) = - \frac{E}{{k_{\mathrm{B}}T}} + \frac{{\mathrm{\Delta }E_{\mathrm{F}}}}{{k_{\mathrm{B}}T}}$$
#
# The latter assumption can only be valid for values $E > E_\mathrm{G}$, i.e. everything is absorbed for energies above bandgap, so the linear fit is made for values around the inflection point, above the bandgap.
#
# [Source](https://www.nature.com/articles/s41560-018-0219-8)

# %% [markdown]
# ## Imports

# %%
from scipy.signal import find_peaks
from scipy.signal import peak_widths
from matplotlib import pyplot as plt
import pandas as pd
import sys

from bric_analysis_libraries.pl import pl_analysis as pla
from bric_analysis_libraries import standard_functions as std
from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries.pl import pl_analysis as bpa
from bix_analysis_libraries.thot import export_asset
from bix_analysis_libraries.plotly import export_plotly

from thot import ThotProject

from plotly import express as px

# %% [markdown]
# Functions
# %%


def plot_PL(data):
    pdf = data.copy()
    pdf.columns = pdf.columns.get_level_values('pixel')
    y_max = pdf.loc[1.5:1.9].max().values[0]
    range_y = (-0.1 * y_max, 1.1 * y_max)
    fig = px.line(
        pdf,
        range_x=(1.5, 1.9),
        range_y=range_y,
        labels={
            'energy': 'energy / eV',
            'value': 'photon flux / (m<sup>-2</sup> s<sup>-1</sup> eV<sup>-1</sup>)',
            'color': 'pixel',
        },
        title=sub
    )
    return fig


# %%
db = ThotProject(dev_root='../../../../evap_pero/data/2021-11-16/PL')
asset = db.find_asset({'type': 'PL_df'})

# %%
df = pd.read_pickle(asset.file)
# take reference as a separate variable
ref = df['white']
df = df.drop('white', axis=1)
df.columns = df.columns.droplevel('param')
df.head()

# %% [markdown]
# ## PL plot

# %%
for sub, data in df.groupby('substrate', axis=1):
    fig = plot_PL(data)
    export_asset(f'PL_plot_{sub}.html', db, export_plotly, fig, 'PL_plot')
# %% [markdown]
# ## Calculation

# %%
excitation_range = (2.3, 2.36)
emission_range = (1.5, 1.9)

# %%
dfs = []
fits = {}
for name, data in df.groupby(axis=1, level=df.columns.names):
    fit = bpa.high_energy_tail_fit(data, 0.015, *emission_range)
    fits[name] = fit

    sub = data.columns.get_level_values('substrate')[0]
    pix = data.columns.get_level_values('pixel')[0]
    fig = bpa.plot_hetf(data, fit, *emission_range)
    export_asset(
        f'HETF_plot_{sub}_{pix}.html',
        db,
        export_plotly,
        fig,
        'HETF_plot'
    )

fits = pd.concat(fits, names=df.columns.names)
fits.index = fits.index.droplevel('energy')
fits.head()

# %%
metrics = pd.DataFrame()
metrics['QFLS_HETF/V'] = fits['qfls', 'value']
metrics['bandgap_PL/eV'] = pla.peak_position(df, *emission_range)
metrics['FWHM_PL/eV'] = pla.fwhm(df, *emission_range)
metrics['PLQY'] = bpa.calculate_plqy(
    df,
    ref,
    emission_range,
    excitation_range
)
metrics.head()

# %%
props = {
    'file': 'PL_metrics.pkl',
    'type': 'PL_metrics',
    'tags': ['PL', 'metrics']
}
asset_path = db.add_asset(props, 'PL_metrics')
pd.to_pickle(metrics, asset_path)
metrics.to_csv(bsf.change_extension(asset_path, 'csv'))


# %%
sys.exit()

# %%
# %% [markdown]
# ---

# %%

# %%
std.set_plot_defaults()

# %%
pdf = df.loc[1.3: 2.2]
for name, data in pdf.groupby(axis=1, level=df.columns.names):
    prominence = 0.1 * float(data.loc[1.5: 1.9].max())
    print(prominence)
    x = data[name].values
    peaks, _ = find_peaks(x, prominence=[prominence, None])
    print(data.iloc[peaks])
    results_half = peak_widths(x, peaks, rel_height=1.0)
    plt.plot(x)
    plt.plot(peaks, x[peaks], "x")
    plt.axhline(prominence, color="gray")
    plt.hlines(*results_half[1:], color="C2")
    plt.show()


# %%


# %%


# %%
# # old
# def fit_lin(df, t_qfls_guess=(300, 1), t_bound=[299, 301], **kwargs):
#     '''
#     :param t_bound: Tuple of lower and upper bounds for temperature.
#     '''
#     def calc_beta(x):
#         kb = phys.physical_constants['Boltzmann constant in eV/K'][0]
#         return - 1 / (x * kb)

#     beta_bound = [calc_beta(t) for t in t_bound]
#     bounds = ((beta_bound[0], -np.inf), (beta_bound[1], np.inf))

#     guess = []
#     guess.append(calc_beta(t_qfls_guess[0]))
#     guess.append(guess[0] * t_qfls_guess[1])

#     def lin_reg(x, a, b):
#         return a * x + b

#     fit = std.df_fit_function(lin_reg, guess=guess, bounds=bounds, **kwargs)
#     return fit(df)

# def fit_wurfel(df, **kwargs):
#     '''
#     '''
#     def wurfel_fit(E, qfls, T):
#         kb = phys.physical_constants['Boltzmann constant in eV/K'][0]
#         h = phys.physical_constants['Planck constant in eV/Hz'][0]
#         return 2 * phys.pi * E ** 2 / (h ** 3 * phys.c ** 2 * np.exp((E - qfls) / (kb * T)) - 1)

#     fit = std.df_fit_function(wurfel_fit, **kwargs)
#     return fit(df)

# def calc_hetf(data, fit):
#     t = fit['t', 'value'].values [0]
#     qfls = fit['qfls', 'value'].values [0]

#     def calc(x):
#         kb = phys.physical_constants['Boltzmann constant in eV/K'][0]
#         h = phys.physical_constants['Planck constant in eV/Hz'][0]
#         return 2 * phys.pi * x.index.values ** 2 / (h ** 3 * phys.c ** 2 * np.exp((x.index.values - qfls) / (kb * t)))
#     return data.apply(lambda x: calc(x))

# name = list(name)
# name[-1] = 'fit'
# name = tuple(name)

# data[name] = data
# dfs.append(data)

# dfs = pd.concat(dfs, axis=1)
