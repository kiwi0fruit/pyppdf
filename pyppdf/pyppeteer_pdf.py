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
        >>> # Choose page.goto behaviour. By default pyppdf tries 'url' mode then 'setContent' mode.
        >>> # 'url' works only if site arg was provided or {goto={url=<...>}} was set in the merged args.
        >>> # 'setContent' (without page.goto), 'temp' (temp file) and 'data-text-html' work only with
        >>> # stdin input. 'setContent' and 'data-text-html' presumably do not support some remote
        >>> # content. I have bugs with the last one when: page.goto(f'data:text/html,{html}')
        >>> #
    dir_ :
        Directory for goto temp mode.
    """
    _launch = get_args('launch', args, {})
    _goto = get_args('goto', args, {})
    url = _goto.kwargs.pop('url', url)
    emulatemedia = get_args('emulateMedia', args)
    waitfor = get_args('waitFor', args)
    pdf = get_args('pdf', args, {})
    if output_file:
        output_file = p.abspath(p.expandvars(p.expanduser(output_file)))
        if dir_ is None:
            dir_ = p.dirname(output_file)
        pdf.kwargs.setdefault('path', output_file)

    temp_file = None

    def get_url():
        nonlocal temp_file
        if url and (not goto or goto == 'url'):
            if p.isfile(url):
                return pathlib.Path(url).as_uri()
            return url
        elif html and (not goto or goto == 'setContent'):
            return None

        elif html and (goto == 'temp') and dir_:
            _temp_file = p.join(dir_, '__temp__.html')
            _url = pathlib.Path(_temp_file).as_uri()
            print(html, file=open(_temp_file, 'w', encoding='utf-8'))
            temp_file = _temp_file
            return _url

        elif html and (goto == 'data-text-html'):
            return f'data:text/html,{html}'
        else:
            raise PyppdfError(
                'Incompatible goto mode, or neither url nor html args were set.\n' +
                f'goto: {goto}, dir_: {dir_}, url[:20]: {url[:20]}, html[:20]: {html[:20]}'
            )

    url = get_url()
    browser = await launch(*_launch.args, **_launch.kwargs)

    try:
        page = await browser.newPage()
        if url:
            await page.goto(url, *_goto.args, **_goto.kwargs)
        else:
            await page.setContent(html)

        if emulatemedia.args is not None:
            await page.emulateMedia(*emulatemedia.args, **emulatemedia.kwargs)
        if waitfor.args is not None:
            await page.waitFor(*waitfor.args, **waitfor.kwargs)

        ret = await page.pdf(**pdf.kwargs)

        if temp_file:
            os.remove(temp_file)
        await browser.close()
        return ret
    except Exception as e:
        if temp_file:
            os.remove(temp_file)
        await browser.close()
        raise e


def save_pdf(output_file: str=None, url: str=None, html: str=None,
             args_dict: Union[str, dict]=None,
             args_upd: Union[str, dict]=None,
             goto: str=None, dir_: str=None) -> bytes:
    """
    Converts html document to pdf via pyppeteer
    and writes to disk if asked. Also returns bytes of pdf.

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
        dict with *additional* pyppeteer kwargs or Python code str that would
        be "litereval" evaluated to the dictionary.
        This dict would be recursively merged with args_dict.
    goto :
        Same as in 'main' function.
    dir_ :
        Directory for goto temp mode.
    """
    if args_dict is None:
        args_dict = litereval(ARGS_DICT)
    elif isinstance(args_dict, str):
        args_dict = litereval(args_dict)
    if not isinstance(args_dict, dict):
        raise TypeError(f'Invalid pyppdf `args_dict` arg (should be a dict): {args_dict}')

    if args_upd is not None:
        args_upd = litereval(args_upd) if isinstance(args_upd, str) else args_upd
        if not isinstance(args_upd, dict):
            raise TypeError(f'Invalid pyppdf `args_upd` arg (should be a dict): {args_upd}')
        args_dict = merge(args_upd, args_dict, copy=True)

    return asyncio.get_event_loop().run_until_complete(
        main(args=args_dict, url=url, html=html,
             output_file=output_file, goto=goto, dir_=dir_)
    )
    

ARGS_DICT = docstr_defaults(save_pdf, 0)
GOTO = litereval(docstr_defaults(main, 0))
GOTO_HELP = docstr_defaults(main, 1)


@click.command(help=f"""Reads html document, converts it to pdf via
pyppeteer and writes to disk (or writes base64 encoded pdf to stdout).

PAGE is an URL or a common file path, pyppdf reads from stdin if PAGE is not set.

-a, --args defaults:

{re.sub(r'^ +', '', ARGS_DICT, flags=re.MULTILINE)}

They affect the following pyppeteer methods (only the last name should be used):
pyppeteer.launch, page.goto, page.emulateMedia, page.waitFor, page.pdf. See:

https://miyakogi.github.io/pyppeteer/reference.html#pyppeteer.page.Page.pdf
""")
@click.argument('page', type=str, default=None, required=False)
@click.option('-a', '--args', 'args_dict', type=str, default=None,
              help='Python code str that would be evaluated to the dictionary that is a ' +
                   'pyppeteer functions options. Has predefined defaults.')
@click.option('-u', '--upd', 'args_upd', type=str, default=None,
              help="Same as --args dict but --upd dict is recursively merged into --args.")
@click.option('-o', '--out', type=str, default=None,
              help='Output file path. If not set then pyppdf writes base64 encoded pdf to stdout.')
@click.option('-d', '--dir', 'dir_', type=str, default=None,
              help="Directory for '--goto temp' mode. Has priority over dir of the --out")
@click.option('-g', '--goto', type=click.Choice(list(GOTO)), default=None, help=GOTO_HELP)
def cli(page, args_dict, args_upd, out, dir_, goto):
    url, html = (page, None) if page else (None, sys.stdin.read())
    ret = save_pdf(output_file=out, args_dict=args_dict, args_upd=args_upd,
                   goto=goto, url=url, html=html, dir_=dir_)
    if not out:
        import base64
        sys.stdout.write('data:application/pdf;base64,' + 
                         base64.b64encode(ret).decode("utf-8"))
