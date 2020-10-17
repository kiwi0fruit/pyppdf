from setuptools import setup, find_packages

import os
import io
import versioneer

here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='pyppdf',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),

    description='Pyppeteer PDF. Print html sites and files to pdf via pyppeteer (uses patched pyppeteer that by default downloads updated Chromium revision via https with certifi).',
    long_description=long_description,
    long_description_content_type="text/markdown",

    url='https://github.com/kiwi0fruit/pyppdf',

    author='Peter Zagubisalo',
    author_email='peter.zagubisalo@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],

    # keywords='sample setuptools development',
    packages=find_packages(exclude=['docs', 'tests']),
    python_requires='>=3.6',
    install_requires=['certifi', 'click', 'psutil', 'litereval>=0.0.9', 'pyppeteer>=0.2.2'],

    entry_points={
        'console_scripts': [
            'pyppdf=pyppdf.pyppeteer_pdf:cli',
            'pyppdf-install=pyppdf.install:install',
        ],
    },
)
