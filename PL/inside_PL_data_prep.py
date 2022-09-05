# %%
from bix_analysis_libraries import (
    thot as bt,
    plotly as bp
)
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries.pl import pl_data_prep as pldp
import pandas as pd
from plotly import express as px

# %%


def import_file(file):
    df = pd.read_csv(
        file,
        sep='\t',
        skiprows=17,
        encoding='mbcs',
        index_col=0,
        names=['wavelength/nm', 'flux [photons/(cm2 s nm)]', 'counts/s'],
        usecols=['wavelength/nm', 'flux [photons/(cm2 s nm)]']
    )
    return df


# %%
db = bt.init_thot(__file__)
df = ppdp.import_raw_data(db, import_file)
df = pldp.df_to_energy(df)
df = df * 10000  # convert from cm-2 to m-2
df = df.rename(
    columns={'flux [photons/(cm2 s nm)]': 'flux [photons/(m2 s eV)]'},
    level='param'
)
df.head()
# %%
plot_df = df.droplevel(['date', 'param'], axis=1)
name = ['_'.join(col) for col in plot_df.columns.values]
plot_df = pd.concat([plot_df], axis=1, keys=name, names=[
                    'name', 'substrate', 'pixel'])
plot_df = plot_df.stack(['substrate', 'pixel'])
plot_df = plot_df.reset_index(['substrate', 'pixel'])
plot_df.head()
# %%
fig = px.line(
    plot_df,
    color='substrate',
    line_dash='pixel'
)
fig.update_layout(
    xaxis_title='energy / eV',
    yaxis_title="photon flux / m<sup>-2</sup> s<sup>-1</sup> eV<sup>-1</sup>"
)
bt.export_asset('PL_plot.html', db, bp.export_plotly, fig)
