# %%
import pandas as pd
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from plotly import express as px
from bix_analysis_libraries import plotly as bp
# %%


def import_file(file):
    df = pd.read_csv(
        file,
        sep=' ',
        skiprows=1,
        index_col=0,
        names=['2theta', 'intensity']
    )
    return df


# %%
db = bt.init_thot(__file__)
df = ppdp.import_raw_data(db, import_file)
df.head()
# %%
bt.export_asset('XRD_df.pkl', db, pd.to_pickle, df)
# %%
plot_df = df.droplevel(['date', 'param'], axis=1)
fig = px.line(plot_df)
fig.update_layout(
    xaxis_title='2<i>&#920;</i> / &deg;',
    yaxis={
        'title': 'intensity',
        'showticklabels': False,
        'showgrid': False,
        'ticks': ''
    }
)
fig.show()
bp.export_plotly(fig, 'XRD_plot.html')
