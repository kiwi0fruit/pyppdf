pyppdf: Pyppeteer PDF
=====================

Prints html sites and files to pdf via pyppeteer (uses patched pyppeteer
that by default downloads updated Chromium revision via https with
certifi). I use it with
`Pandoctools/Knitty <https://github.com/kiwi0fruit/pandoctools>`__.

Pyppeteer is a Python port of the Puppeteer.

CLI
===

Command line interface:

::

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

     https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pd
     f

   Options:
     -a, --args TEXT               Python code str that would be evaluated to the
                                   dictionary that is a pyppeteer functions
                                   options. Has predefined defaults.
     -u, --upd TEXT                Same as --args dict but --upd dict is
                                   recursively merged into --args.
     -o, --out TEXT                Output file path. If not set then writes to
                                   stdout.
     -s, --self-contained BOOLEAN  Set when then there is no remote content.
                                   Performance will be opitmized for no remote
                                   content. Has priority over --temp.
     -t, --temp BOOLEAN            Whether to use temp file in case of stdin
                                   input.
     --help                        Show this message and exit.

See `Pyppeteer
methods <https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf>`__.

Python API
==========

::

   def save_pdf(output_file: str=None, site: str=None, src: str=None,
                args_dict: Union[str, dict]=None,
                args_upd: Union[str, dict]=None,
                self_contained: bool=False,
                temp: bool=False) -> Union[str, None]:
       """
       Converts html document to pdf via pyppeteer
       and writes to disk (or returns base64 encoded str of pdf).

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
       output_file :
           Path to write pdf to.
           If None then returns returns base64 encoded str of pdf.
       site :
           Site address or html document file path
           (site has priority over src).
       src :
           html document file source
           (site has priority over src).
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
       self_contained :
          If True then there is no remote content. Performance will be opitmized if no remote content.
          Has priority over temp.
       temp :
           Whether to use temp file in case of src input and no site.
       """

.. code:: py

   async def main(args: dict, url: str=None, html: str=None, output_file: str=None,
                  self_contained: bool=False) -> Union[bytes, None]:
       """
       Returns bytes of pdf or None

       Parameters
       ----------
       args :
           Pyppeteer options that govern conversion.
           dict with keys dedicated for pyppeteer functions used.
       url :
           Site address or html document file path
           (url, that can also be set in args, has priority over src).
       html :
           html document file source
       output_file :
           Path to save pdf. If None then returns bytes of pdf.
       self_contained :
           If True then there is no remote content.
           Performance will be opitmized if no remote content.
       """
