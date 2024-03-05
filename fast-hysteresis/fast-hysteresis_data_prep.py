# %%
import pandas as pd
from plotly import express as px
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import plotly as bp
from bix_analysis_libraries.pero_pipes import data_prep as ppdp
from bix_analysis_libraries import bix_standard_functions as bsf


# %%
def import_file(file):
    columns = pd.MultiIndex.from_product(
        [
            [
                "<i>V</i><sub>OC</sub> / V",
                "<i>J</i><sub>SC</sub> / mA cm<sup>&#8722;2</sup>",
                "FF / %",
                "PCE / %",
            ],
            ["rev", "for"],
        ],
        names=["param", "direction"],
    )
    df = pd.read_csv(file, sep="\t", index_col=0)
    print(df.columns)
    df.columns = columns
    return df


db = bt.init_thot(__file__)
df = ppdp.import_raw_data(db, import_file, has_date=False, rename_axis=False)
df.index.name = "scan rate / V s<sup>&#8722;1</sup>"
df = df.stack(["param", "direction"])
df = bsf.flatten_column_index(df)
df = df.sort_index(level="direction")
df = df.reset_index(["param", "direction"])
df.head()
# %%
fig = px.line(
    df,
    # x="thickness",
    # y="value",
    # color="template",
    log_x=True,
    facet_col="param",
    line_dash="direction",
    facet_col_wrap=2,
    markers=True,
    facet_col_spacing=0.1,
    facet_row_spacing=0.10,
)
fig.update_yaxes(matches=None, showticklabels=True)
fig.update_layout(legend=dict(yanchor="top", y=1, xanchor="left", x=1.03, title=None))
fig.update_yaxes(
    title_text="<i>J</i><sub>SC</sub> / mA cm<sup>&#8722;2</sup>", row=2, col=1
)
fig.update_yaxes(title_text="<i>V</i><sub>OC</sub> / V", row=2, col=2)
fig.update_yaxes(title_text="FF / %", row=1, col=1)
fig.update_yaxes(title_text="PCE / %", row=1, col=2)
# fig.show()

_ = bt.export_asset("fast-hysteresis_overview_plot.html", db, bp.export_plotly, fig)
