# %%
from pathlib import Path
import pandas as pd

from bix_analysis_libraries import thot as bt, bix_standard_functions as bsf
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries.eqe import eqe_analysis as bea

from bric_analysis_libraries.pl import pl_data_prep as pdp

# %%
db = bt.init_thot(__file__)
df = ppdp.import_formatted_data(db, {"type": "EQE_tandem_df"})
df = pdp.index_to_energy(df)
df.index.name = "energy / eV"
df.head()
# %%
am = bt.import_global_asset(
    db,
    a_path=r"root:/../scripts/common/EQE/reference_spectra/AM1.5G.pkl",
    dev_path=Path(r"reference_spectra/AM1.5G.pkl"),
    a_type="AM1.5G",
    import_function=pd.read_pickle,
)

am.head()

# %%
jsc = bea.calc_Jsc(df, am)
jsc = jsc.unstack("subcell")
ppdp.pickle_w_markdown(jsc, "EQE_tandem_metrics", db, ".1f")
