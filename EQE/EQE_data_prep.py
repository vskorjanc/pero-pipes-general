# %%
import pandas as pd
from plotly import express as px

from bix_analysis_libraries import (
    plotly as bp,
    thot as bt,
    bix_standard_functions as bsf
)
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bric_analysis_libraries.pl import pl_data_prep as pdp

# %% [markdown]
# Functions
# %%


def import_outside_eqe(db):
    def import_file(file):
        df = pd.read_csv(
            file,
            sep='\t',
            skiprows=5,
            usecols=[0, 1],
            names=['wavelength/nm', 'EQE'],
            index_col='wavelength/nm'
        )
        return df
    # The pattern maches everything before a dot or '_AM 1'
    df = ppdp.import_raw_data(db, import_file, pattern=r'.+?(?=(?:_AM 1|\.))')
    return df


def import_niama2_eqe(db):
    def import_file(file):
        df = pd.read_csv(
            file,
            sep='\t',
            skiprows=range(10),
            names=['wavelength/nm', 'measured', 'EQE'],
            usecols=['wavelength/nm', 'EQE'],
            index_col=0
        )
        return df
    df = ppdp.import_raw_data(db, import_file)
    return df


def import_EQE(db):
    assets = bt.find_assets(db)
    if '.TRQ' in assets[0].file:
        df = import_niama2_eqe(db)
    else:
        df = import_outside_eqe(db)
    return df


# %%
db = bt.init_thot(__file__)
df = import_EQE(db)
# switch from percent to fraction
df = df.apply(lambda x: x / 100)
df.head()

# %%
plot_df = df.droplevel(['date', 'param'], axis=1)
plot_df = bsf.flatten_column_index(plot_df)
plot_df.head()
fig = px.line(plot_df)
bt.export_asset('EQE_plot.html', db, bp.export_plotly, fig)

# %%
e_df = pdp.index_to_energy(df).sort_index()
e_df.index.name = 'energy/eV'
e_df.head()

# %%
bt.export_asset('EQE_df.pkl', db, pd.to_pickle, e_df)
