# %%
from bix_analysis_libraries import thot as bt
import pandas as pd
import sys
import re

# %%

db = bt.init_thot(__file__)
# %%
asset = db.find_asset(search={"type": "substrate_meta"})
if asset:
    df = pd.read_pickle(asset.file)
    df = df.loc[("general", "group")]
    df = df.to_dict()
    groups = {}
    for substrate, group in df.items():
        groups[group] = groups.get(group, []) + [substrate]
    colors = db.find_asset(search={"type": "groups_meta"})
    if colors:
        colors_df = pd.read_pickle(colors.file)
else:
    container = db.find_container({"type": "JV"})
    if "groups" not in container.metadata:
        container = db.find_container({"type": "batch"})
    try:
        groups = container.metadata["groups"]
    except KeyError:
        sys.exit()
# %%
assets = []
plot_types = [
    "MPP_plot",
    "EQE_plot",
    "FTPS_plot",
    "XRD_plot",
    "XRD_stacked_plot",
    "XRD_comparison_plot",
    "PL_plot",
    "R-T_plot",
    "EQE_reflectance_plot_all",
    "tandem_JV_plot",
    "tr-SPV_line_plot",
    "tr-PL_plot",
    "J_sc_intensity_plot",
    "V_oc_intensity_plot",
    "FF_intensity_plot",
    "fast-hysteresis_overview_plot",
]
for plot_type in plot_types:
    assets += bt.find_assets(db, search={"type": plot_type}, exit=False)

# %%

for asset in assets:
    with open(asset.file, "r+") as f:
        html = f.read()
        for name, substrates in groups.items():
            if colors:
                color = colors_df.loc[name]["color"]
            if not isinstance(substrates, list):
                substrates = list(substrates)
            for substrate in substrates:
                html = re.sub(
                    f', {{0,1}}"name": {{0,1}}"{substrate}(_.){{0,1}}(, .*?){{0,1}}"',
                    f',"name": "{name}"',
                    html,
                )
                if colors:
                    html = re.sub(
                        rf'"({substrate}(?:_.){{0,1}})(?:, .*?)","line":{{"color":"#.{{6}}"',
                        rf'"\1","line":{{"color":"{color}"',
                        html,
                    )
        f.seek(0)
        f.write(html)
        f.truncate()
