# %%
import pandas as pd

# %%


def import_file(file):
    with open(file) as fd:
        headers = [next(fd) for i in range(4)]
        df = pd.read_csv(fd, sep='\t', names=[
            'wavelength', 'counts'], index_col=0)
    return df


def open_row_file(file):
    with open(file, 'r') as f:
        return eval(f.readline())


# %%
# opening calibration and dark offset curves
offset = open_row_file('darkAsRow.txt')
calib = open_row_file('calibSplitterStellar_pro_asRow.txt')
# %%
df = import_file('example_pl.txt')
df['offset'] = offset
df['calib'] = calib
df = df.drop('counts', axis=1)
# %%
pd.to_pickle(df, 'BQY_calib_df.pkl')
