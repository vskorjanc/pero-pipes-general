# %%
from bix_analysis_libraries import thot as bt
import datetime
import os


# %%
def create_iframe(asset_name, container_name, root_path):
    file = os.path.join(root_path, container_name, asset_name, asset_name)
    file = f"{file}.html"
    iframe = f'<iframe border=0 frameborder=0 height=550 width=700 src="file:{file}"> </iframe>'
    return iframe


# %%
db = bt.init_thot(__file__)

# %%
current_path = os.getcwd()
batch_path = os.path.dirname(current_path)
folder_name = os.path.basename(batch_path)
markdown_file_name = f"{folder_name}.md"
markdown_file_path = os.path.join(batch_path, markdown_file_name)
markdown_file_path
# %%
if os.path.exists(markdown_file_path):
    exit()
# %%
today = datetime.date.today()
formatted_date = today.strftime("%Y-%m-%d")
formatted_date

# %% iframes

# evap
log_plot = create_iframe("log_plot", "evap_logs", batch_path)
pressure_temp_log_plot = create_iframe(
    "pressure-temp_log_plot", "evap_logs", batch_path
)
source_hist_log_plot = create_iframe("source-hist_log_plot", "evap_logs", batch_path)

# In-situ PL
in_situ_PL_heatmap_plot = create_iframe(
    "in-situ_PL_heatmap_plot", "in-situ_PL", batch_path
)
in_situ_PL_spectral_plot = create_iframe(
    "in-situ_PL_spectral_plot", "in-situ_PL", batch_path
)

# JV
JV_scans_plot = create_iframe("JV-scans_plot", "JV", batch_path)
grouped_boxplot = create_iframe("grouped_boxplot", "JV", batch_path)
tandem_JV_plot = create_iframe("tandem_JV_plot", "tandem_JV", batch_path)


# MPP
MPP_plot = create_iframe("MPP_plot", "MPP", batch_path)
tandem_MPP_plot = create_iframe("MPP_plot", "tandem_MPP", batch_path)


# EQE
EQE_analysis_plot = create_iframe("EQE_analysis_plot", "EQE", batch_path)
EQE_plot = create_iframe("EQE_plot", "EQE", batch_path)
EQE_reflectance_plot = create_iframe(
    "EQE_reflectance_plot", "tandem_optical", batch_path
)
EQE_reflectance_plot_all = create_iframe(
    "EQE_reflectance_plot_all", "tandem_optical", batch_path
)

# PL
PL_plot = create_iframe("PL_plot", "inside_PL", batch_path)

# XRD
XRD_plot = create_iframe("XRD_plot", "XRD", batch_path)

# %%
markdown_content = f"""---
tags: [batch]
date: {formatted_date}
---

## Motivation

## Details

## Comments

## Process

### Presets

![[evap_logs/recipe_sources/recipe_sources.md]]

![[evap_logs/recipe_specs/recipe_specs.md]]

### Logs

![[evap_logs/source_metrics/source_metrics.md]]

![[evap_logs/chamber_metrics/chamber_metrics.md]]

{log_plot}

{source_hist_log_plot}

{pressure_temp_log_plot}

### In-situ measurements

#### PL

{in_situ_PL_heatmap_plot}

{in_situ_PL_spectral_plot}

## Measurements - single junction

### JV

{grouped_boxplot}

{JV_scans_plot}

[[JV/JV_metrics/JV_metrics.md|JV_metrics]]

### MPP

{MPP_plot}

### EQE

{EQE_plot}

{EQE_analysis_plot}

![[EQE/EQE_metrics/EQE_metrics.md]]

### PL

{PL_plot}

![[inside_PL/PL_metrics/PL_metrics.md]]

### XRD

{XRD_plot}

### SEM

## Measurements - tandem

### JV

{tandem_JV_plot}

[[tandem_JV/raw_JV_metrics/raw_JV_metrics.md|raw_JV_metrics]]

### MPP

{tandem_MPP_plot}

### EQE / reflectance

{EQE_reflectance_plot}

{EQE_reflectance_plot_all}

![[optical_tandem/EQE_tandem/EQE_tandem_metrics/EQE_tandem_metrics.md]]

"""
# %%
with open(markdown_file_path, "w") as file:
    file.write(markdown_content)
