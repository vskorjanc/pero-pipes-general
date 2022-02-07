# %% [markdown]
# Created: October 2021
# Author: Viktor Skorjanc
# E-mail: viktor.skorjanc@gmail.com

# %% [markdown]
# # PL data prep

# %% [markdown]
# ## Imports

# %%
import pandas as pd
from io import StringIO
from xml.etree import ElementTree as ET
import re
import sys

from plotly import express as px


from thot import ThotProject
from bix_analysis_libraries import bix_standard_functions as bsf
from bric_analysis_libraries.pl import pl_data_prep as pldp

# %%
thot = ThotProject(dev_root='../../data/238/PL_mapping')
raw = thot.find_asset({'type': 'PL_mapping_spectra'})
meta = thot.find_asset({'type': 'PL_mapping_meta'})

# %% [markdown]
# ## Functions

# %% [markdown]
# ## Analysis

# %% [markdown]
# Fetch metadata

# %%
data = ''
with open(meta.file, "rb") as f:
    for line in f:
        line.strip()
        line.decode('utf-8', 'ignore')
        data += str(line)
mtch = re.compile('(<Info[\s\S]+<\/Info>)').search(data)[1]

# %%
tree = ET.ElementTree(ET.fromstring(mtch))
root = tree.getroot()

x_items = root[0][1][1]
x_points = int(x_items[3][1].text)
x_step = float(x_items[2][1].text.replace(',', '.'))

y_items = root[0][2][1]
y_points = int(y_items[3][1].text)
y_step = float(y_items[2][1].text.replace(',', '.'))


# %% [markdown]
# Fetch data

# %%
with open(raw.file, 'r') as f:
    data = f.read()

# %%
frames = data.split('Frame ')
frames.pop(0)

# %%
df = []
for (num, frame) in enumerate(frames):
    try:
        data = pd.read_csv(StringIO(frame), names=[
                           'wavelength', 'intensity'], skiprows=[0, 1], index_col=0)
        data = pldp.index_to_energy(data, scale=True)
    except TypeError as t:
        data = pd.read_csv(StringIO(frame), sep='\t', names=[
                           'wavelength', 'intensity'], skiprows=[0, 1], index_col=0)
        data = pldp.index_to_energy(data, scale=True)

    x = ((x_points - num - 1) % x_points) * x_step / 10
    y = (num // x_points) * y_step / 10
    data = bsf.add_levels(data, [x, y], ['x/cm', 'y/cm'])
    df.append(data)

df = pd.concat(df)
df.index = df.index.set_names('E/eV', level=-1)
df.head()

# %%
df.tail()

# %%
props = {
    'file': 'PL_mapping_df.pkl',
    'type': 'PL_mapping_df',
    'tags': ['PL', 'df']
}
asset_path = thot.add_asset(props, 'PL_mapping_df')
pd.to_pickle(df, asset_path)

# %%
sys.exit()

# %% [markdown]
# ---

# %%
for (x, data) in df.groupby(level='x'):
    af = data.index.get_level_values('y')
    x = data.index.get_level_values('wavelength')
    ymax = data['intensity'].max()
    fig = px.scatter(data, x=x, y='intensity',
                     animation_frame=af, range_y=[0, ymax])
    break
fig.show()
fig.write_html('test/PL.html', auto_play=False)

# %%


# %%
ymax

# %%
