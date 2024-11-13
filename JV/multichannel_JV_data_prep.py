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
def remove_header(zip_file, file_name):
    with zip_file.open(file_name) as f:
        # Decode the file content to a string, then split into lines
        lines = f.read().decode("ISO-8859-15").splitlines()
        # Find the starting line with "## Data ##"
        for line_number, line in enumerate(lines):
            if "## Data ##" in line:
                data_start_line = line_number + 1  # Start after "## Data ##"
                break
        # Join the lines starting from the data start line and load into StringIO for pandas
        data = "\n".join(lines[data_start_line:])
    file_wo_header = StringIO(data)
    return file_wo_header


def import_mpp(file, substrate, pixel):
    mpp = pd.read_csv(
        file,
        sep="\t",
        skiprows=1,
        index_col=0,
        names=[
            "time / s",
            "voltage / V",
            "current_density / (mA cm-2)",
            "power / (mW cm-2)",
        ],
    )
    # convert hours to seconds
    mpp.index = mpp.index.map(lambda x: x * 3600)
    mpp.columns.name = "param"
    # reorder levels
    mpp = mpp[["power / (mW cm-2)", "voltage / V", "current_density / (mA cm-2)"]]
    mpp = bsf.add_levels(
        mpp, [substrate, pixel, ""], ["substrate", "pixel", "date"], axis=1
    )
    return mpp


def import_scan(file, substrate, pixel):
    scans = pd.read_csv(file, sep="\t", skiprows=5, usecols=range(4))
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
        skiprows=2,
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
jv_pattern = (
    r"0001_\d{4}-\d{2}-\d{2}_\d{2}.\d{2}.\d{2}_Stability \(JV\)_(.+)_\d{1,2}[ABC]\.txt"
)
mpp_pattern = (
    r"0000_\d{4}-\d{2}-\d{2}_\d{2}.\d{2}.\d{2}_Stability \(Tracking\)_(.+)\.txt"
)


# %%
db = bt.init_thot(__file__)
asset = bt.find_assets(db)[0]
# %%
zip_file = zipfile.ZipFile(asset.file)
info_list = zip_file.infolist()
mpps = []
scans = []
raw_metrics = []
for item in info_list:
    file_name = item.filename
    base_name = os.path.basename(file_name)
    parent_folder = os.path.basename(os.path.dirname(file_name))
    pixel = parent_folder[-1].lower()

    jv_match = re.match(jv_pattern, base_name)
    mpp_match = re.match(mpp_pattern, base_name)
    if mpp_match:
        substrate = mpp_match.groups()[0]
        mpp_file = remove_header(zip_file, file_name)

        mpp = import_mpp(mpp_file, substrate, pixel)
        mpps.append(mpp)

    if jv_match:
        substrate = jv_match.groups()[0]

        jv_file = remove_header(zip_file, file_name)

        scan = import_scan(jv_file, substrate, pixel)
        # remove duplicate index values
        scan = scan.loc[~scan.index.duplicated(), :].copy()
        scans.append(scan)

        jv_file = remove_header(zip_file, file_name)
        raw_metric = import_metrics(jv_file, substrate, pixel)
        raw_metrics.append(raw_metric)

zip_file.close()
mpps = pd.concat(mpps, axis=1)
mpps = mpps.sort_index()
bt.export_asset("MPP_df.pkl", db, pd.to_pickle, mpps)
mpps.head()
# %%
scans = pd.concat(scans, axis=1)
scans = scans.stack("pixel", future_stack=True)
scans = bsf.add_level(scans, "", "date")
scans = scans.reorder_levels(["Voltage", "date", "pixel", "direction"])
scans = scans.sort_index()
bt.export_asset("JV_scans.pkl", db, pd.to_pickle, scans)
scans
# %%
raw_metrics = pd.concat(raw_metrics)
raw_metrics["FF"] = raw_metrics["FF"].where(lambda x: x < 90)
raw_metrics = raw_metrics.sort_index()
ppdp.pickle_w_markdown(raw_metrics, "raw_JV_metrics", db, floatfmt=".2f")
raw_metrics
