from setuptools import setup, find_packages

import os
import versioneer

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='pyppdf',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),

    description='Pyppeteer PDF. Print html sites and files to pdf via pyppeteer (uses patched pyppeteer that by default downloads updated Chromium revision via https with certifi).',
    long_description=long_description,

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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    # keywords='sample setuptools development',
    packages=find_packages(exclude=['docs', 'tests']),

    install_requires=['certifi', 'click', 'litereval>=0.0.3', 'pyppeteer>=0.0.25'],
)
