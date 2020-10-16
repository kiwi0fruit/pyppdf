import os
import platform
# Check the latest stable Chromium revision here: https://chromium.woolyss.com/
# Then find out the real revision for download (OS specific):
# https://github.com/Bugazelle/chromium-all-old-stable-versions/blob/master/chromium.stable.csv
rev = dict(Windows='800229', Linux='800217', Darwin='800208').get(platform.system(), '800218')
os.environ.setdefault('PYPPETEER_CHROMIUM_REVISION', rev)
from .patch_pyppeteer import patch_pyppeteer
patch_pyppeteer()
