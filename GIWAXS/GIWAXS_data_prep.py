# %%
import pandas as pd
import numpy as np
from plotly import express as px

from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.xrd import xrd_data_prep as bx
from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries import bix_standard_functions as bsf
# %%


def import_file(file):
    df = pd.read_csv(
        file,
        sep=';',
        index_col=[0, 1],
        decimal=',',
    )
    df.columns = df.columns.astype(np.float64)
    df.columns.name = 'Angle/deg'
    df = bx.subtract_background(df)
    df = df.apply(lambda x: x / x.max())
    return df


# %%
db = bt.init_thot(__file__)
asset = db.find_asset(search={'type': ''})
df = import_file(asset.file)
df.head()
# %%
# for XRD comparison plot (determine phase of initial, middle and end)
pkl_export = df.droplevel('q/mn-1')
pkl_export = pkl_export[[0.05, 1, 2]]
pkl_export.columns.name = 'substrate'
pkl_export.index.name = '2theta'
pkl_export = bsf.add_levels(pkl_export, ['', ''], ['param', 'date'], axis=1)
bt.export_asset('XRD_df.pkl', db, bsf.export_pickle, pkl_export)
pkl_export.head()
# %%
# for substrate comparison
# from bix_analysis_libraries.pero_pipes import data_prep as ppdp
# df = ppdp.import_raw_data(db, import_file, has_date=False, rename_axis=False)
# df = df.stack('substrate')
# df.head()
# %%
plot_df = df.droplevel('q/mn-1')
for zmax in [0.3, 1]:
    hm_fig = px.imshow(
        plot_df.T,
        zmax=zmax,
        origin='lower',
        aspect='auto',
        labels={'color': 'Intensity'}
    )
    bt.export_asset(f'heatmap_plot_i{zmax}.html', db, bp.export_plotly, hm_fig)
# %%
# px.imshow(plot_df)
plot_df = plot_df.stack(0)
plot_df.name = 'Intensity'
plot_df = plot_df.reset_index([
    'Angle/deg',
    # 'substrate'
])
line_fig = px.line(
    plot_df,
    animation_frame='Angle/deg',
    # color='substrate'
)
# line_fig.show()
_ = bt.export_asset('GIWAX_line_plot.html', db, bp.export_plotly, line_fig)
