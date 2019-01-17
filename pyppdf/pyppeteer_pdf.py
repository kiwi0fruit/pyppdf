# should pass output path as parameter for to pdf exporter
import click
import sys
import os
import os.path as p
import pathlib
import asyncio
from typing import Union
import ast
import copy
import re
from litereval import litereval, merge
# noinspection PyUnresolvedReferences
from .patch_pyppeteer import patch_pyppeteer
from pyppeteer import launch


async def main(args: dict, temp_url: str, output_file: str):
    browser = await launch()
    page = await browser.newPage()

    goto_kwargs = args.get('goto', {})
    goto_kwargs.pop('url', None)
    waitfor_args = args.get('waitFor')
    pdf_kwargs = args.get('pdf', {})
    pdf_kwargs.pop('path', None)

    await page.goto(url=temp_url, **goto_kwargs)
    if waitfor_args is not None:
        await page.waitFor(*waitfor_args)
    await page.pdf(path=output_file, **pdf_kwargs)

    await browser.close()


def save_pdf(inp: str, out: str, args: Union[str, dict]='{}'):
    """
    Converts html document to pdf via pyppeteer
    and writes to disk.

    ``args`` example:

    >>> "{goto={timeout=100000}, waitFor=[1],
    >>>   pdf={printBackground=True}}"

    Parameters
    ----------
    inp :
        html document
    out :
        path to write pdf to
    args :
        dict with pyppeteer kwargs or Python code str that would
        be evaluated to the dictionary.
        All keys are optional: 'goto' and 'pdf' values are dict,
        'waitFor' value is a tuple.
    """
    args = litereval(args) if isinstance(args, str) else args
    if not isinstance(args, dict):
        raise TypeError(f'Invalid pyppeteer arguments (should be a dict): {args}')

    output_file = p.abspath(p.expandvars(p.expanduser(out)))
    temp_file = p.join(p.dirname(output_file),
                       f'__temp__{p.basename(output_file)}.html')
    temp_url = pathlib.Path(temp_file).as_uri()
    print(inp, file=open(temp_file, 'w', encoding='utf-8'))

    try:
        asyncio.get_event_loop().run_until_complete(
            main(args, temp_url, output_file)
        )
        os.remove(temp_file)
    except Exception as e:
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
