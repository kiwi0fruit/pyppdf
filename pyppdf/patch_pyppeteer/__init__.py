import os
os.environ.setdefault('PYPPETEER_CHROMIUM_REVISION', '693954')
from .patch_pyppeteer import patch_pyppeteer
patch_pyppeteer()
