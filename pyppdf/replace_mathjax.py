import sys
import re


def replace_mathjax(
        html: str,
        mathjax_url: str="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/latest.js?config=TeX-MML-AM_CHTML"
):
    return re.sub(
        r"<script[^<]+?[Mm]ath[Jj]ax.+?</script>",
        f"<script src=\"{mathjax_url}\" async></script>",
        html, flags=re.DOTALL)


def main():
    kwargs = {}
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == '--help':
            print('Replaces MathJax script section with URL only script. ' +
                  'First arg is optional custom MathJax URL. ' +
                  'Reads from stdin and writes to stdout.')
            return
        else:
            kwargs = dict(mathjax_url=sys.argv[1])
    sys.stdout.write(replace_mathjax(sys.stdin.read(), **kwargs))


if __name__ == '__main__':
    main()
