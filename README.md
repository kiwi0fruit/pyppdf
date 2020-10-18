# pyppdf: Pyppeteer PDF

[![Build Status](https://travis-ci.org/kiwi0fruit/pyppdf.svg?branch=master)](https://travis-ci.org/kiwi0fruit/pyppdf)

Prints html sites and files to pdf via pyppeteer (uses patched pyppeteer that by default downloads updated Chromium revision via https with certifi). I use it with  [Pandoctools/Knitty](https://github.com/kiwi0fruit/pandoctools).

Pyppeteer is a Python port of the Puppeteer. pyppdf command line interface is built with the help of [litereval](https://github.com/kiwi0fruit/litereval) and click.

At the moment recommended settings when reading from stdin are following:

```bash
echo "# Header
Text \$f(x)=x^2\$" |
pandoc -f markdown -t html --standalone --self-contained |
pyppdf -o doc.pdf --goto temp
```


# Contents:

* [Install](#install)
* [CLI](#cli)
  * [pyppdf](#pyppdf)
  * [pyppdf-install](#pyppdf-install)
* [Python API](#python-api)


# Install

Needs python 3.6+

### conda install:

```bash
conda install -c defaults -c conda-forge pyppdf
```

### pip install:

```bash
pip install pyppdf
```

### Linux

If on Ubuntu additionally install ([Chrome headless doesn't launch on Unix](https://github.com/puppeteer/puppeteer/blob/main/docs/troubleshooting.md#chrome-headless-doesnt-launch-on-unix)):

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libgcc1 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 libxtst6 lsb-release wget xdg-utils
```


# CLI

### pyppdf

Command line interface:

```
Usage: pyppdf [OPTIONS] [PAGE]

  Reads html document, converts it to pdf via pyppeteer and writes to disk
  (or writes base64 encoded pdf to stdout).

  PAGE is an URL or a common file path, pyppdf reads from stdin if PAGE is
  not set.

  -a, --args defaults:

  {launch={args=['--font-render-hinting=none']},goto={waitUntil='networkidle0',
  timeout=100000}, pdf={width='8.27in', printBackground=True, margin={top='1in',
  right='1in', bottom='1in', left='1in'},}}

  They affect the following pyppeteer methods (only the last name should be
  used):  pyppeteer.launch, page.goto, page.emulateMedia,
  page.waitForNavigation, page.waitFor, page.pdf. See:

  https://pyppeteer.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf

Options:
  -a, --args TEXT  Python code str that would be evaluated to the dictionary
                   that is a pyppeteer functions options. Has predefined
                   defaults.
  -u, --upd TEXT   Same as --args dict but --upd dict is recursively merged
                   into --args.
  -o, --out TEXT   Output file path. If not set then pyppdf writes base64
                   encoded pdf to stdout.
  -d, --dir TEXT   Directory for '--goto temp' mode. Has priority over dir of
                   the --out

  -g, --goto [url|setContent|temp|data-text-html]
                   Choose page.goto behaviour. By default pyppdf tries 'url'
                   mode then 'setContent' mode. 'url' works only if url (PAGE)
                   arg was provided or {goto={url=<...>}} was set in the merged
                   args. 'setContent' (works without page.goto), 'temp' (temp
                   file) and 'data-text-html' work only with stdin input.
                   'setContent' and 'data-text-html' presumably do not support
                   some remote content. I have bugs with the last one
                   when: page.goto(f'data:text/html,{html}')
  --help           Show this message and exit.

```

See [Pyppeteer methods](https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf).


### pyppdf-install

Simply downloads and installs Chromium beforehead (uses fresher revision from pyppdf):

```bash
pyppdf-install
```


# Python API

```
def save_pdf(output_file: str=None, url: str=None, html: str=None,
             args_dict: Union[str, dict]=None,
             args_upd: Union[str, dict]=None,
             goto: str=None, dir_: str=None) -> bytes:
    """
    Converts html document to pdf via pyppeteer
    and writes to disk if asked. Also returns bytes of pdf.

    ``args_dict`` affect the following methods that are used during
    conversion (only the last name should be used):
    ``pyppeteer.launch``, ``page.goto``, ``page.emulateMedia``,
    ``page.waitForNavigation``, ``page.waitFor``, ``page.pdf``. See:
     https://pyppeteer.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf

    ``args_dict`` default value:

    >>> # {launch={args=['--font-render-hinting=none']},
    >>> #  goto={waitUntil='networkidle0', timeout=100000},
    >>> #  pdf={width='8.27in', printBackground=True,
    >>> #       margin={top='1in', right='1in',
    >>> #               bottom='1in', left='1in'},}}
    >>> #

    ``args_upd`` examples that won't overwrite other options:

    * ``"{launch={args=['--no-sandbox', '--disable-setuid-sandbox']}}``
    *  ``"{emulateMedia="screen", waitFor=1000}"``

    Formats for **values** of the ``args_dict``:
    ``*args`` and ``**kwargs`` for functions:

    * ``{(): (arg1, arg2), kwarg1=val1, kwarg2=val2}``
      Special key for positional args,
    * ``[arg1, arg2]`` or ``(arg1, arg2)`` Positional only,
    * If value in the **root**  ``args_dict`` is None
      (like ``{foo=None}``) it later means that ``'foo'`` key is not used
      (same as if it was absent in the **root** dict).

    Parameters
    ----------
    output_file :
        Path to write pdf to.
    url :
        Page URL address or html document file path
        (url has priority over html).
    html :
        html document file source
        (url has priority over html).
    args_dict :
        Options that govern conversion.
        dict with pyppeteer kwargs or Python code str that would
        be "litereval" evaluated to the dictionary.
        If None then default values are used.
        Supports extended dict syntax: {foo=100, bar='yes'}.
    args_upd :
        dict with *additional* pyppeteer kwargs or Python code str
        that would be "litereval" evaluated to the dictionary.
        This dict would be recursively merged into args_dict.
    goto :
        Same as in 'main' function.
    dir_ :
        Directory for goto temp mode.
    """
```

```py
async def main(args: dict, url: str=None, html: str=None, output_file: str=None,
               goto: str=None, dir_: str=None) -> bytes:
    """
    Returns bytes of pdf.

    Parameters
    ----------
    args :
        Pyppeteer options that govern conversion.
        dict with keys dedicated for pyppeteer functions used.
        See save_pdf for more details.
    url :
        Site address or html document file path (url - that by the
        way can also be set in args - has priority over html).
    html :
        html document file source
    output_file :
        Path to save pdf
    goto :
        One of:
        >>> # ('url', 'setContent', 'temp', 'data-text-html')
        >>> #
        >>> # Choose page.goto behaviour. By default pyppdf tries 'url' mode
        >>> # then 'setContent' mode. 'url' works only if url (PAGE) arg was
        >>> # provided or {goto={url=<...>}} was set in the merged args.
        >>> # 'setContent' (works without page.goto), 'temp' (temp file) and
        >>> # 'data-text-html' work only with stdin input. 'setContent' and
        >>> # 'data-text-html' presumably do not support some remote
        >>> # content. I have bugs with the last one when:
        >>> # page.goto(f'data:text/html,{html}')
        >>> #
    dir_ :
        Directory for goto temp mode.
    """
```
