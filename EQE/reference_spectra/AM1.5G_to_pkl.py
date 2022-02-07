# %%
import pandas as pd
import scipy.constants as phys

from bix_analysis_libraries.pl import pl_data_prep as bpdp

# %%
am = pd.read_csv(
    'ASTMG173.csv',
    header=1,
    index_col=0,
    names=['wavelength/nm', 'AM0', 'AM1.5G/(W m-2 nm-1)', 'AM1.5'],
    usecols=['wavelength/nm', 'AM1.5G/(W m-2 nm-1)'],
)
am = bpdp.df_to_energy(am)  # from nm-1 to eV-1
am = am.apply(lambda x: x / (x.index * phys.e))  # from W to photons / s
am = am.rename(
    {'AM1.5G/(W m-2 nm-1)': 'AM1.5G/(photons s-1 m-2 eV-1)'},
    axis=1
)
am.head()

# %%
pd.to_pickle(am, 'AM1.5G.pkl')
