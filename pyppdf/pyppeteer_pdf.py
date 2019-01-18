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


def docstr_defaults(func, i: int):
    """
    From ``func`` docstr reads and strips ``i``-th multiline
    block of the form (strips it to ``'<...>'`` contents only):

    >>> # <...>
    >>> # <...>
    >>> #
    """
    return re.sub(r' +>>> # ', '', re.findall(
        r'(?<=>>> # ).+?(?=\r?\n +>>> #\r?\n)',
        str(func.__doc__),
        re.DOTALL)[i])


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
    _launch = get_args('launch', args, {})
    _goto = get_args('goto', args, {})
    url = _goto.kwargs.pop('url', url)
    emulatemedia = get_args('emulateMedia', args)
    waitfor = get_args('waitFor', args)
    pdf = get_args('pdf', args, {})
    if output_file:
        pdf.kwargs.setdefault('path', output_file)

    def get_goto():
        if url and (not goto or goto == 'url'):
            return 'url'
        elif html and (not goto or goto == 'setContent'):
            return 'setContent'
        elif html and output_file and (not goto or goto == 'temp'):
            return 'temp'
        elif html and goto == 'data-text-html':
            return 'data-text-html'
        elif url:
            return 'url'
        elif html:
            return 'setContent'
        else:
            raise PyppdfError('Either url or html arg should be set.')

    goto = get_goto()
    browser = await launch(*_launch.args, **_launch.kwargs)
    temp_file = None

    try:
        page = await browser.newPage()
        if goto == 'setContent':
            await page.setContent(html)
        else:
            if goto == 'url':
                pass
            elif goto == 'data-text-html':
                url = f'data:text/html,{html}'
            elif goto == 'temp':
                _temp_file = p.join(p.dirname(output_file),
                                    f'__temp__{p.basename(output_file)}.html')
                print(html, file=open(_temp_file, 'w', encoding='utf-8'))
                temp_file = _temp_file
                url = pathlib.Path(temp_file).as_uri()
            else:
                raise PyppdfError('Unknown bug')
            await page.goto(url, *_goto.args, **_goto.kwargs)

        if emulatemedia.args is not None:
            await page.emulateMedia(*emulatemedia.args, **emulatemedia.kwargs)
        if waitfor.args is not None:
            await page.waitFor(*waitfor.args, **waitfor.kwargs)

        ret = await page.pdf(**pdf.kwargs)

        if temp_file:
            os.remove(temp_file)
        await browser.close()
        if not ('path' in pdf.kwargs):
            return ret
    except Exception as e:
        if temp_file:
            os.remove(temp_file)
        await browser.close()
        raise e


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

    url, html = None, None
    if site:
        if p.isfile(site):
            url = pathlib.Path(site).as_uri()
        else:
            url = site
    elif src:
        html = src
    else:
        raise PyppdfError('Either site or src arg should be set.')

    bytes_pdf = asyncio.get_event_loop().run_until_complete(
        main(args=args_dict, url=url, html=html, output_file=output_file, goto=goto)
    )
    if bytes_pdf is not None:
        import base64
        return 'data:application/pdf;base64,' + base64.b64encode(bytes_pdf).decode("utf-8")


ARGS_DICT = docstr_defaults(save_pdf, 0)
GOTO = litereval(docstr_defaults(main, 0))
GOTO_HELP = docstr_defaults(main, 1)


@click.command(help=f"""Reads html document, converts it to pdf via
pyppeteer and writes to disk (or writes base64 encoded pdf to stdout).

SITE is a site url of a file path, pyppdf reads from stdin if SITE is not set.

-a, --args defaults:

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
              help='Output file path. If not set then pyppdf writes base64 encoded pdf to stdout.')
@click.option('-g', '--goto', type=click.Choice(list(GOTO)), default=None, help=GOTO_HELP)
def cli(site, args_dict, args_upd, out, goto):
    kwargs = dict(site=site) if site else dict(src=sys.stdin.read())
    ret = save_pdf(output_file=out, args_dict=args_dict, args_upd=args_upd,
                   goto=goto, **kwargs)
    if ret:
        sys.stdout.write(ret)
