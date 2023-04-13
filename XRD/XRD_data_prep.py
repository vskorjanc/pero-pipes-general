# %%
import pandas as pd
import zipfile
import xml.etree.ElementTree as ET

from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries.xrd import xrd_data_prep as bx
# %%


def import_xy(file):
    df = pd.read_csv(
        file,
        sep=' ',
        skiprows=1,
        index_col=0,
        names=['2theta', 'intensity']
    )
    return df


def import_brml(file):
    brml = zipfile.ZipFile(file)
    xml_string = brml.read('Experiment0/RawData0.xml')
    root = ET.fromstring(xml_string)
    data_xml = root.findall("DataRoutes/DataRoute/Datum")
    data = ([child.text.split(',')[2:] for child in data_xml])
    df = pd.DataFrame(data, columns=['2theta', 'theta', 'intensity'])
    df = df.astype(float)
    df = df.set_index('2theta')
    df = df.drop('theta', axis=1)
    return df


def import_xrd(db):
    assets = bt.find_assets(db)
    if '.xy' in assets[0].file:
        df = ppdp.import_raw_data(db, import_xy)
    else:
        df = ppdp.import_raw_data(db, import_brml)
        df = bx.subtract_background(df)
    return df


# %%
db = bt.init_thot(__file__)
df = import_xrd(db)
df = df.apply(lambda x: x / x.max())
df.head()
# %%
bt.export_asset('XRD_df.pkl', db, pd.to_pickle, df)
