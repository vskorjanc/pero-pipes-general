# %%
from bix_analysis_libraries import thot as bt
import re

# %%

db = bt.init_thot(__file__)
container = db.find_container({'type': 'JV'})
groups = container.metadata['groups']

# %%
assets = []
plot_types = [
    'MPP_plot',
    'EQE_plot',
    'FTPS_plot',
    'XRD_plot',
    'XRD_comparison_plot',
    'PL_plot',
    'R-T_plot'
]
for plot_type in plot_types:
    assets += bt.find_assets(db, search={'type': plot_type}, exit=False)

# %%

for asset in assets:
    with open(asset.file, 'r+') as f:
        html = f.read()
        for name, substrates in groups.items():
            if not isinstance(substrates, list):
                substrates = list(substrates)
            for substrate in substrates:
                html = re.sub(
                    f', {{0,1}}"name": {{0,1}}"{substrate}(_.){{0,1}}"',
                    f',"name": "{name}"',
                    html
                )
        f.seek(0)
        f.write(html)
        f.truncate()
