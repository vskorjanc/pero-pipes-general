# %%
from PIL import Image
from bix_analysis_libraries import thot as bt
from bix_analysis_libraries import bix_standard_functions as bsf
import os
# %%
db = bt.init_thot(__file__)
assets = bt.find_assets(db)
if not os.path.exists('converted'):
    os.mkdir('converted')

# %%
for asset in assets:
    img = Image.open(asset.file)
    rgb_img = img.convert('RGB')
    file_name = os.path.basename(asset.file)
    new_name = bsf.change_extension(file_name, 'jpg')
    path = os.path.join('converted', new_name)
    rgb_img.save(path)
