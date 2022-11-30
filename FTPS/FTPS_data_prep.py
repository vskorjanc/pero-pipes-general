# %%
import pandas as pd
from plotly import express as px

from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
# %%


def import_file(path):
    df = pd.read_csv(
        path,
        skiprows=2,
        sep='\t',
        usecols=[0, 2],
        names=['energy / eV', 'EQE / %'],
        index_col='energy / eV'
    )
    return df


# %%
db = bt.init_thot(__file__)
df = ppdp.import_raw_data(db, import_file, pattern=r'[^_]*_[a-z]')
df.head()
# %%
plot_df = df.droplevel(['date', 'param'], axis=1)
plot_df = bsf.flatten_column_index(plot_df)
fig = px.line(
    plot_df,
    log_y=True,
)
fig.update_yaxes(title='EQE / %')
fig.update_layout(legend_title='substrate')
fig.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            direction="left",
            buttons=list([
                dict(
                    args=["yaxis.type", "log"],
                    label="log",
                    method="relayout"
                ),
                dict(
                    args=["yaxis.type", "linear"],
                    label="linear",
                    method="relayout"
                )
            ]),
            pad={"r": 10, "t": 10},
            showactive=True,
            x=0.11,
            xanchor="left",
            y=1.1,
            yanchor="top"
        ),
    ]
)
bt.export_asset('FTPS_plot.html', db, bp.export_plotly, fig)
