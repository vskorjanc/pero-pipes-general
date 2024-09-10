# %%
# TODO convert the HTML text to latex
from bix_analysis_libraries import thot as bt
from PIL import Image
from matplotlib import pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar
import os
from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries.pero_pipes import data_prep as ppdp

# %%
db = bt.init_thot(__file__)
assets = bt.find_assets(db)
groups = ppdp.import_formatted_data(db, {"type": "substrate_meta"})
groups = groups.loc[("general", "group")]
groups = groups.to_dict()
groups
# %%
colors = ppdp.import_formatted_data(db, {"type": "groups_meta"})
colors = colors["color"].to_dict()
colors


# %%
def get_substrate_name(path):
    file_name = os.path.basename(path)
    substrate = file_name.split("_")[0]
    if "." in substrate:
        substrate = file_name.split(".")[0]
    return substrate


def get_nm_per_px(img):
    lines = img.tag[34118][0]
    lines = lines.split("\n")
    for line in lines:
        if line[0:8] != "Width = ":
            continue
        width_in_um = line[8:13]
    width_in_nm = float(width_in_um) * 1000
    nm_per_pixel = width_in_nm / img.width
    return nm_per_pixel


def plot_img(path):
    img = Image.open(path)
    fig, ax = plt.subplots()
    ax_img = ax.imshow(img)
    plt.axis("off")

    nm_per_pixel = get_nm_per_px(img)

    sb = ScaleBar(
        nm_per_pixel,
        "nm",
        label=label,
        length_fraction=0.3,
        color="white",
        frameon=True,
        border_pad=1,
        font_properties={
            "size": 18,
        },
        # scale_loc="top",
        box_color=color,
        box_alpha=0.8,
        location="lower right",
    )
    ax.add_artist(sb)
    return fig


# %%
if not os.path.exists("converted"):
    os.mkdir("converted")
# %%
for asset in assets:
    substrate = get_substrate_name(asset.file)
    label = groups[substrate]
    color = colors[label]
    if "<sub>" in label:
        label = label.replace("<sub>", "$_")
        label = label.replace("</sub>", "$")

    fig = plot_img(asset.file)

    file_name = os.path.basename(asset.file)
    new_name = bsf.change_extension(file_name, "jpg")
    path = os.path.join("converted", new_name)
    plt.tight_layout()
    fig.savefig(path, bbox_inches="tight", pad_inches=0.0, dpi=250)
    plt.close()
