import os
# Check the latest stable Chromium revision here: https://chromium.woolyss.com/
# But there is some OS specific stuff:
# https://github.com/Bugazelle/chromium-all-old-stable-versions/blob/master/chromium.stable.csv
if os.name == 'nt':
  rev = '782793'
else:
  rev = '782793'
os.environ.setdefault('PYPPETEER_CHROMIUM_REVISION', rev)
from .patch_pyppeteer import patch_pyppeteer
patch_pyppeteer()
