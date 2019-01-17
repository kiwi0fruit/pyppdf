import click
import sys
import os
import os.path as p
import pathlib
import asyncio
from typing import Union
from litereval import litereval, merge
# noinspection PyUnresolvedReferences
from .patch_pyppeteer import patch_pyppeteer
from .api_helper import get_args_kwargs
from pyppeteer import launch


class PyppdfError(Exception):
    pass


async def main(args: dict, url: str, output_file: str):
    launch_ = get_args_kwargs('launch', args, {})
    goto = get_args_kwargs('goto', args, {})
    goto[1].pop('url', None)
    waitfor = get_args_kwargs('waitFor', args, None)
    pdf = get_args_kwargs('pdf', args, {})
    pdf[1].pop('path', None)

    browser = await launch(*launch_[0], **launch_[1])
    page = await browser.newPage()

    await page.goto(url=url, *goto[0], **goto[1])
    if waitfor[0] is not None:
        await page.waitFor(*waitfor[0], **waitfor[1])
    await page.pdf(path=output_file, *pdf[0], **pdf[1])

    await browser.close()


def save_pdf(out: str, site: str=None, src: str=None, args_dict: Union[str, dict]=None,
             args_upd: Union[str, dict]=None) -> None:
    r"""
    Converts html document to pdf via pyppeteer
    and writes to disk.

    ``args_dict`` formats for ``*args`` and ``**kwargs`` for functions:
        * ``{(): (arg1, arg2), kwarg1=val1, kwarg2=val2}``
        * ``[arg1, arg2]`` or ``(arg1, arg2)``
        * ``{kwarg1=val1, kwarg2=val2}``
        * ``{foo=None}`` means that ``'foo'`` key is not used
          (same as if it was absent).

    ``args_dict`` default value:

    >>> # {goto={waitUntil='networkidle0', timeout=100000},
    >>> #  pdf={width='8.27in', printBackground=True,
    >>> #       margin={top='1in', right='1in',
    >>> #               bottom='1in', left='1in'},}}

    ``args_upd`` example that won't overwrite another options:

    ``"{launch={args=['--no-sandbox', '--disable-setuid-sandbox']}, waitFor=[1000]}"``

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
        args_dict = dict(goto=dict(waitUntil='networkidle0',
                                   timeout=100000),
                         pdf=dict(width='8.27in',
                                  printBackground=True,
                                  margin=dict(top='1in', right='1in',
                                              bottom='1in', left='1in'),))
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
    _src = src and isinstance(site, str)
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


@click.command(help="Reads html document from stdin, converts it to pdf via " +
                    "pyppeteer and writes to disk.")
@click.argument('output_path', type=str)
@click.option('-d', '--dict', 'args', type=str, default='{}',
              help='Python code str that would be evaluated to the dictionary ' +
                   'that is a pyppeteer options. Options are read from (optional) ' +
                   'keys like this: "dict(goto=dict(timeout=100000), waitFor=(1,), ' +
                   'pdf=dict(printBackground=True))" goto and pdf values are dict, ' +
                   'waitFor value is a tuple.')
def cli(output_path, args):
    save_pdf(sys.stdin.read(), output_path, args)
