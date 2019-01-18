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

     Reads html document, converts it to pdf via pyppeteer and writes to disk
     (or writes base64 encoded pdf to stdout).

     SITE is a site url of a file path, pyppdf reads from stdin if SITE is not
     set.

     -a, --args defaults:

     {goto={waitUntil='networkidle0', timeout=100000}, pdf={width='8.27in',
     printBackground=True, margin={top='1in', right='1in', bottom='1in',
     left='1in'},}}

     They affect the following pyppeteer methods (only the last name should be
     used): pyppeteer.launch, page.goto, page.emulateMedia, page.waitFor,
     page.pdf. See:

     https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pd
     f

   Options:
     -a, --args TEXT                 Python code str that would be evaluated to
                                     the dictionary that is a pyppeteer functions
                                     options. Has predefined defaults.
     -u, --upd TEXT                  Same as --args dict but --upd dict is
                                     recursively merged into --args.
     -o, --out TEXT                  Output file path. If not set then pyppdf
                                     writes base64 encoded pdf to stdout.
     -g, --goto [url|setContent|temp|data-text-html]
                                     Choose page.goto behaviour. By default
                                     pyppdf tries modes in the listed order.
                                     pyppdf uses default order if user set mode
                                     cannot be applied.
                                     'url' works only if site
                                     arg was provided or {goto={url=<...>}} was
                                     set in merged args.
                                     'setContent' (without
                                     page.goto), 'temp' (temp file) and 'data-
                                     text-html' work only with
                                     stdin input.
                                     'setContent' and 'data-text-html' presumably
                                     do not support some remote
                                     content. I have
                                     bugs with the last one though:
                                     page.goto(f'data:text/html,{html}')
     --help                          Show this message and exit.

See `Pyppeteer
methods <https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf>`__.

Python API
==========

::

   def save_pdf(output_file: str=None, site: str=None, src: str=None,
                args_dict: Union[str, dict]=None,
                args_upd: Union[str, dict]=None,
                goto: str=None) -> Union[str, None]:
       """
       Converts html document to pdf via pyppeteer
       and writes to disk (or returns base64 encoded str of pdf).

       ``args_dict`` affect the following methods (only the last name should be used):
       ``pyppeteer.launch``, ``page.goto``, ``page.emulateMedia``, ``page.waitFor``, ``page.pdf``.
       See: https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf

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
       goto:
           Same as in 'main' function.
       """

.. code:: py

   async def main(args: dict, url: str=None, html: str=None, output_file: str=None,
                  goto: str=None) -> Union[bytes, None]:
       """
       Returns bytes of pdf or None.

       Parameters
       ----------
       args :
           Pyppeteer options that govern conversion.
           dict with keys dedicated for pyppeteer functions used.
       url :
           Site address or html document file path
           (url, that can also be set in args, has priority over html).
       html :
           html document file source
       output_file :
           Path to save pdf. If None then returns bytes of pdf.
       goto :
           One of:
           >>> # ('url', 'setContent', 'temp', 'data-text-html')
           >>> #
           >>> # Choose page.goto behaviour. By default pyppdf tries modes in the listed order.
           >>> # pyppdf uses default order if user set mode cannot be applied.
           >>> # 'url' works only if site arg was provided or {goto={url=<...>}} was set in merged args.
           >>> # 'setContent' (without page.goto), 'temp' (temp file) and 'data-text-html' work only with
           >>> # stdin input. 'setContent' and 'data-text-html' presumably do not support some remote
           >>> # content. I have bugs with the last one though: page.goto(f'data:text/html,{html}')
           >>> #
       """
