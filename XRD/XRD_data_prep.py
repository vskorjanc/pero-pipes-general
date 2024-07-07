# %%
import pandas as pd
import zipfile
import xml.etree.ElementTree as ET
from plotly import express as px

from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries.xrd import xrd_data_prep as bx
from bix_analysis_libraries import plotly as bp

# %%


def import_xy(file):
    df = pd.read_csv(
        file, sep=" ", skiprows=1, index_col=0, names=["2theta", "intensity"]
    )
    return df


def import_brml(file):
    brml = zipfile.ZipFile(file)
    xml_string = brml.read("Experiment0/RawData0.xml")
    root = ET.fromstring(xml_string)
    data_xml = root.findall("DataRoutes/DataRoute/Datum")
    data = [child.text.split(",")[2:] for child in data_xml]
    df = pd.DataFrame(data, columns=["2theta", "theta", "intensity"])
    df = df.astype(float)
    df = df.set_index("2theta")
    df = df.drop("theta", axis=1)
    return df


def import_xrd(db):
    assets = bt.find_assets(db)
    if ".xy" in assets[0].file:
        df = ppdp.import_raw_data(db, import_xy)
    else:
        df = ppdp.import_raw_data(db, import_brml)
    return df


# %%
db = bt.init_thot(__file__)
df = import_xrd(db)
# %%
plot_df = df.droplevel(["date", "param"], axis=1)
fig = px.line(plot_df)
fig.update_layout(xaxis_title="2<i>&#920;</i> / &deg;", yaxis_title="intensity")
fig.update_yaxes(showticklabels=False, showgrid=False, ticks="")
fig.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            direction="left",
            buttons=list(
                [
                    dict(
                        args=["yaxis.type", "linear"], label="linear", method="relayout"
                    ),
                    dict(args=["yaxis.type", "log"], label="log", method="relayout"),
                ]
            ),
            pad={"r": 10, "t": 10},
            showactive=True,
            x=0.11,
            xanchor="left",
            y=1.1,
            yanchor="top",
        ),
    ]
)
fig.show()
bt.export_asset("non-normalized_XRD_plot.html", db, bp.export_plotly, fig)
# %%
df = bx.subtract_background(df)
df = df.apply(lambda x: x / x.max())
df.head()
# %%
bt.export_asset("XRD_df.pkl", db, pd.to_pickle, df)
