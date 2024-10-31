# %%
from io import StringIO
import pandas as pd
import zipfile
from bix_analysis_libraries import thot as bt
import os.path
import re
from bix_analysis_libraries import bix_standard_functions as bsf
from bix_analysis_libraries.pero_pipes import data_prep as ppdp


# %%
def import_scan(file, substrate, pixel):
    scans = pd.read_csv(file, sep="\t", skiprows=35, usecols=range(4))
    columns = pd.MultiIndex.from_product(
        [["for", "rev"], ["Voltage", substrate]], names=["direction", ""]
    )
    scans.columns = columns
    scans = scans.stack("direction", future_stack=True)
    scans = scans.set_index("Voltage", append=True)
    scans = scans.droplevel(0)
    scans = bsf.add_level(scans, pixel, "pixel", axis=1)
    scans = scans.dropna()
    return scans


def import_metrics(file, substrate, pixel):
    raw_metrics = pd.read_csv(
        file,
        sep="\t",
        skiprows=32,
        names=[
            "V_oc",
            "J_sc",
            "V_MPP",
            "J_MPP",
            "P_MPP",
            "R_ser",
            "R_par",
            "FF",
            "PCE",
        ],
        nrows=2,
        index_col=0,
    )
    raw_metrics = raw_metrics.rename({"FW": "for", "RV": "rev"})
    raw_metrics.index.name = "direction"
    raw_metrics = bsf.add_levels(
        raw_metrics, [substrate, "", pixel], ["substrate", "date", "pixel"]
    )
    raw_metrics = raw_metrics.drop("P_MPP", axis=1)
    return raw_metrics


# %%
regex_pattern = (
    r"0001_\d{4}-\d{2}-\d{2}_\d{2}.\d{2}.\d{2}_Stability \(JV\)_(.+)_\d{1,2}[ABC]\.txt"
)

# %%
db = bt.init_thot(__file__)
asset = bt.find_assets(db)[0]
# %%
zip_file = zipfile.ZipFile(asset.file)
info_list = zip_file.infolist()
scans = []
raw_metrics = []
for item in info_list:
    file_name = item.filename
    base_name = os.path.basename(file_name)
    parent_folder = os.path.basename(os.path.dirname(file_name))
    pixel = parent_folder[-1].lower()

    match = re.match(regex_pattern, base_name)
    if not match:
        continue
    substrate = match.groups()[0]

    jv_data = zip_file.read(file_name)
    jv_data_string = str(jv_data, "ISO-8859-15")

    jv_file = StringIO(jv_data_string)
    scan = import_scan(jv_file, substrate, pixel)
    scans.append(scan)

    jv_file = StringIO(jv_data_string)
    raw_metric = import_metrics(jv_file, substrate, pixel)
    raw_metrics.append(raw_metric)

zip_file.close()

scans = pd.concat(scans, axis=1)
scans = scans.stack("pixel", future_stack=True)
scans = bsf.add_level(scans, "", "date")
scans = scans.reorder_levels(["Voltage", "date", "pixel", "direction"])
scans = scans.sort_index()
bt.export_asset("JV_scans.pkl", db, pd.to_pickle, scans)
scans
# %%
raw_metrics = pd.concat(raw_metrics)
raw_metrics = raw_metrics.sort_index()
ppdp.pickle_w_markdown(raw_metrics, "raw_JV_metrics", db, floatfmt=".2f")
raw_metrics
