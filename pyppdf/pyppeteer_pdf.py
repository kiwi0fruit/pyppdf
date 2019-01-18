import click
import sys
import os
import os.path as p
import pathlib
import asyncio
import re
from typing import Union
from litereval import litereval, merge, get_args
# noinspection PyUnresolvedReferences
from .patch_pyppeteer import patch_pyppeteer
from pyppeteer import launch


class PyppdfError(Exception):
    pass


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
    _launch = get_args('launch', args, {})
    goto = get_args('goto', args, {})
    url = goto.kwargs.pop('url', url)
    emulatemedia = get_args('emulateMedia', args)
    waitfor = get_args('waitFor', args)
    pdf = get_args('pdf', args, {})
    if output_file:
        pdf.kwargs.setdefault('path', output_file)

    browser = await launch(*_launch.args, **_launch.kwargs)
    try:
        page = await browser.newPage()
        if self_contained and html:
            await page.setContent(html)
        else:
            url = url if url else f'data:text/html,{html}'
            await page.goto(url, *goto.args, **goto.kwargs)

        if emulatemedia.args is not None:
            await page.emulateMedia(*emulatemedia.args, **emulatemedia.kwargs)
        if waitfor.args is not None:
            await page.waitFor(*waitfor.args, **waitfor.kwargs)

        ret = await page.pdf(**pdf.kwargs)
        if not ('path' in pdf.kwargs):
            return ret
    except Exception as e:
        await browser.close()
        raise e


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
        Works only if output_file is set.
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

    if output_file:
        output_file = p.abspath(p.expandvars(p.expanduser(output_file)))

    url, html, temp_file = None, None, None
    if site:
        if p.isfile(site):
            url = pathlib.Path(site).as_uri()
        else:
            url = site
    elif src:
        if self_contained:
            html = src
        elif temp and output_file:
            temp_file = p.join(p.dirname(output_file),
                               f'__temp__{p.basename(output_file)}.html')
            url = pathlib.Path(temp_file).as_uri()
            print(src, file=open(temp_file, 'w', encoding='utf-8'))
        else:
            html = src
    else:
        raise PyppdfError('Either site or src arg should be set.')

    try:
        bytes_pdf = asyncio.get_event_loop().run_until_complete(
            main(args=args_dict, url=url, html=html, output_file=output_file,
                 self_contained=self_contained)
        )
        if temp_file:
            os.remove(temp_file)
        if bytes_pdf is not None:
            import base64
            return 'data:application/pdf;base64,' + base64.b64encode(bytes_pdf).decode("utf-8")
    except Exception as e:
        if temp_file:
            os.remove(temp_file)
        raise e


ARGS_DICT = docstr_defaults(save_pdf)


@click.command(help=f"""Reads html document from stdin, converts it to pdf via
pyppeteer and writes to disk (or writes base64 encoded pdf to stdout).
SITE is optional and it's a site url of a file path.

-d, --dict defaults:

{re.sub(r'^ +', '', ARGS_DICT, flags=re.MULTILINE)}

They affect the following pyppeteer methods (only the last name should be used):
pyppeteer.launch, page.goto, page.emulateMedia, page.waitFor, page.pdf. See:

https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf
""")
@click.argument('site', type=str, default=None, required=False)
@click.option('-a', '--args', 'args_dict', type=str, default=None,
              help='Python code str that would be evaluated to the dictionary that is a ' +
                   'pyppeteer functions options. Has predefined defaults.')
@click.option('-u', '--upd', 'args_upd', type=str, default=None,
              help="Same as --args dict but --upd dict is recursively merged into --args.")
@click.option('-o', '--out', type=str, default=None,
              help='Output file path. If not set then writes base64 encoded pdf to stdout.')
@click.option('-s', '--self-contained', type=bool, default=False,
              help='Set when then there is no remote content. ' +
                   'Performance will be opitmized for no remote content. Has priority over --temp.')
@click.option('-t', '--temp', type=bool, default=False,
              help='Whether to use temp file in case of stdin input (works only if --out is set).')
def cli(site, args_dict, args_upd, out, self_contained, temp):
    kwargs = dict(site=site) if site else dict(src=sys.stdin.read())
    ret = save_pdf(output_file=out, args_dict=args_dict, args_upd=args_upd,
                   self_contained=self_contained, temp=temp, **kwargs)
    if ret:
        sys.stdout.write(ret)
