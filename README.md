# pyppdf: Pyppeteer PDF

Prints html sites and files to pdf via pyppeteer (uses patched pyppeteer that by default downloads updated Chromium revision via https with certifi). I use it with  [Pandoctools/Knitty](https://github.com/kiwi0fruit/pandoctools).


# CLI

Command line interface:

```
Usage: pyppdf [OPTIONS] [SITE]

  Reads html document from stdin, converts it to pdf via pyppeteer and
  writes to disk. SITE is optional and it's a site url of a file path.

  -d, --dict defaults:

  {goto={waitUntil='networkidle0', timeout=100000}, pdf={width='8.27in',
  printBackground=True, margin={top='1in', right='1in', bottom='1in',
  left='1in'},}}

  They affect the following pyppeteer methods (only the last name should be
  used): pyppeteer.launch, page.goto, page.emulateMedia, page.waitFor,
  page.pdf. See:

  https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf

Options:
  -d, --dict TEXT  Python code str that would be evaluated to the dictionary
                   that is a pyppeteer functions options. Has predefined
                   defaults.
  -u, --upd TEXT   Same as --dict but --upd dict is recursively merged into
                   --dict.
  -o, --out TEXT   Output file path. Default is "untitled.pdf"
  --help           Show this message and exit.
```

See [Pyppeteer methods](https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf).


# Python API

```
def save_pdf(out: str='untitled.pdf', site: str=None, src: str=None,
             args_dict: Union[str, dict]=None,
             args_upd: Union[str, dict]=None) -> None:
    """
    Converts html document to pdf via pyppeteer
    and writes to disk.

    ``args_dict`` affect the following methods
    (only the last name should be used): ``pyppeteer.launch``, ``page.goto``,
    ``page.emulateMedia``, ``page.waitFor``, ``page.pdf``. See:
      https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf

    ``args_dict`` default value:

    >>> # {goto={waitUntil='networkidle0', timeout=100000},
    >>> #  pdf={width='8.27in', printBackground=True,
    >>> #       margin={top='1in', right='1in',
    >>> #               bottom='1in', left='1in'},}}
    >>> #

    ``args_upd`` example that won't overwrite other options:

    ``"{launch={args=['--no-sandbox', '--disable-setuid-sandbox']}, emulateMedia="screen", waitFor=1000}"``

    ``args_dict`` formats for ``*args`` and ``**kwargs`` for functions:

    * ``{(): (arg1, arg2), kwarg1=val1, kwarg2=val2}``
    * ``[arg1, arg2]`` or ``(arg1, arg2)``
    * ``{kwarg1=val1, kwarg2=val2}``
    * ``{foo=None}`` means that ``'foo'`` key is not used
      (same as if it was absent).

    Parameters
    ----------
    out :
        path to write pdf to
    site :
        site address or html document file path
        (only one from site or src must be defined)
    src :
        html document file source
        (only one from site or src must be defined)
    args_dict :
        Options that govern conversion.
        dict with pyppeteer kwargs or Python code str that would
        be "litereval" evaluated to the dictionary.
        If None then default values are used.
        Supports extended dict syntax: {foo=100, bar='yes'}.
    args_upd :
        dict with *additional* pyppeteer kwargs or Python code str that would
        be "litereval" evaluated to the dictionary.
        This dict would be recursively merged with args_dict.
    """
```
