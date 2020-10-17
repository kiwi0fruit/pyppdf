import os
import platform
# Find out Chromium revision for download (OS specific):
# https://github.com/Bugazelle/chromium-all-old-stable-versions/blob/master/chromium.stable.csv
rev = dict(Windows='800229', Linux='800217', Darwin='800208').get(platform.system(), '800218')  # Only x64 are supported.
os.environ.setdefault('PYPPETEER_CHROMIUM_REVISION', rev)
from .patch_pyppeteer import patch_pyppeteer
patch_pyppeteer()
