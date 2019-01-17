import click
import sys
import os
import os.path as p
import pathlib
import asyncio
import re
from typing import Union
from litereval import litereval, merge, get, args_kwargs
# noinspection PyUnresolvedReferences
from .patch_pyppeteer import patch_pyppeteer
from pyppeteer import launch


class PyppdfError(Exception):
    pass


async def main(args: dict, url: str, output_file: str):
    launch_ = args_kwargs(get('launch', args, {}))
    goto = args_kwargs(get('goto', args, {}))
    goto[1].pop('url', None)
    emulate_media = args_kwargs(get('emulateMedia', args))
    waitfor = args_kwargs(get('waitFor', args))
    pdf = args_kwargs(get('pdf', args, {}))
    pdf[1].pop('path', None)

    browser = await launch(*launch_[0], **launch_[1])
    page = await browser.newPage()

    await page.goto(url, *goto[0], **goto[1])

    if emulate_media[0] is not None:
        await page.emulateMedia(*emulate_media[0], **emulate_media[1])
    if waitfor[0] is not None:
        await page.waitFor(*waitfor[0], **waitfor[1])
    await page.pdf(path=output_file, **pdf[1])

    await browser.close()


def docstr_defaults(func):
    """
    From func docstr reads and strips multiline
    str with ``'<...>'`` contents only:

    >>> # <...>
    >>> # <...>
    >>> #
    """
    return re.sub(r' +>>> # ', '', re.search(
        r'(?<=>>> # ).+?(?=\r?\n +>>> #\r?\n)',
        str(func.__doc__),
        re.DOTALL).group(0))


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
    if args_dict is None:
        args_dict = litereval(ARGS_DICT)
    elif isinstance(args_dict, str):
        args_dict = litereval(args_dict)
    if not isinstance(args_dict, dict):
        raise TypeError(f'Invalid pyppeteer `args_dict` arg (should be a dict): {args_dict}')

    if args_upd is not None:
        args_upd = litereval(args_upd) if isinstance(args_upd, str) else args_upd
        if not isinstance(args_upd, dict):
            raise TypeError(f'Invalid pyppeteer `args_upd` arg (should be a dict): {args_upd}')
        args_dict = merge(args_upd, args_dict, copy=True)

    output_file = p.abspath(p.expandvars(p.expanduser(out)))
    temp_file = None

    _site = site and isinstance(site, str)
    _src = src and isinstance(src, str)
    if (_site and _src) or not (_site or _src):
        raise PyppdfError('Only one from site or src args must be non empty str.')
    elif _src:
        temp_file = p.join(p.dirname(output_file),
                           f'__temp__{p.basename(output_file)}.html')
        url = pathlib.Path(temp_file).as_uri()
        print(src, file=open(temp_file, 'w', encoding='utf-8'))
    elif p.isfile(site):
        url = pathlib.Path(site).as_uri()
    else:
        url = site

    try:
        asyncio.get_event_loop().run_until_complete(
            main(args_dict, url, output_file)
        )
        if temp_file:
            os.remove(temp_file)
    except Exception as e:
        if temp_file:
            os.remove(temp_file)
        raise e


ARGS_DICT = docstr_defaults(save_pdf)


@click.command(help=f"""Reads html document from stdin, converts it to pdf via
pyppeteer and writes to disk. SITE is optional and it's a site url of a file path.

-d, --dict defaults:

{re.sub(r'^ +', '', ARGS_DICT, flags=re.MULTILINE)}

They affect the following pyppeteer methods (only the last name should be used):
pyppeteer.launch, page.goto, page.emulateMedia, page.waitFor, page.pdf. See:

https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf
""")
@click.argument('site', type=str, default=None, required=False)
@click.option('-d', '--dict', 'args_dict', type=str, default=None,
              help='Python code str that would be evaluated to the dictionary that is a ' +
                   'pyppeteer functions options. Has predefined defaults.')
@click.option('-u', '--upd', 'args_upd', type=str, default=None,
              help="Same as --dict but --upd dict is recursively merged into --dict.")
@click.option('-o', '--out', type=str, default='untitled.pdf',
              help='Output file path. Default is "untitled.pdf"')
def cli(site, args_dict, args_upd, out):
    kwargs = dict(site=site) if site else dict(src=sys.stdin.read())
    save_pdf(out=out, args_dict=args_dict, args_upd=args_upd, **kwargs)
