# %%
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd

from bix_analysis_libraries import thot as bt
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries.xrd import xrd_data_prep as bx

# %%


def import_file(file):
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


# %%
db = bt.init_thot(__file__)
df = ppdp.import_raw_data(db, import_file)
df = bx.subtract_background(df)
df = df.apply(lambda x: x/x.max())
df.head()
# %%

_ = bt.export_asset('XRD_df.pkl', db, pd.to_pickle, df)
