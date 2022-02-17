# %%
import pandas as pd
from plotly import express as px

from thot import ThotProject

# %%
db = ThotProject(dev_root='../../../../evap_pero/data/2021-12-15/UV_VIS')
asset = db.find_asset({'type': 'UV-VIS_df'})

# %%
df = pd.read_pickle(asset.file)
df.columns = df.columns.droplevel(['pixel', 'date'])
df = df.stack('substrate')
df.head()


# %%
df['1-R'] = 1 - df['reflectance']
df['1-R-T'] = df['1-R'] - df['transmittance']
df.head()

# %%
for sub, data in df.groupby('substrate'):
    data = data.droplevel('substrate')
    fig = px.line(
        data,
        y=['1-R', '1-R-T'],
        title=sub,
        labels={
            'value': ''
        }
    )
    props = {
        'file': f'R-T_plot_{sub}.html',
        'type': 'R-T_plot',
        'tags': ['UV-VIS', 'R-T', 'plot']
    }
    asset_path = db.add_asset(props, f'R-T_plot_{sub}')
    fig.write_html(asset_path, include_plotlyjs='cdn')
