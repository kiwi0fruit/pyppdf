from typing import Union, Tuple


def get_args_kwargs(name: str, args: dict, default=None) -> Tuple[
    Union[list, None], Union[dict, None]
]:
    """
    Reads *args and **kwars for function/method from a dict.

    >>> from litereval import litereval
    >>> dic = litereval("{func={(): (1, 2), foo=True, bar=100}, foo={(): 'bar'}}")
    >>> func = ([1, 2], {'foo': True, 'bar': 100})
    >>> foo = (['bar'], {})
    >>> assert repr(func) == repr(get_args_kwargs('func', dic))
    >>> assert repr(foo) == repr(get_args_kwargs('foo', dic))
    >>> assert repr(([], {})) == repr(get_args_kwargs('bar', dic, {}))
    >>> assert repr((None, None)) == repr(get_args_kwargs('bar', dic))

    Parameters
    ----------
    name :
        function/method name
    args :
        dict with function/method names as first level keys
    default :
        default fallback value to extract from args

    Returns
    -------
    ret :
        tuple: *args, **kwargs
    """
    name = args.get(name, default)

    def list_(args_) -> list:
        if isinstance(args_, str):
            return [args_]
        try:
            return list(args_)
        except TypeError:
            return [args_]

    if name is None:
        return None, None
    elif isinstance(name, dict):
        _args = name.get((), [])
        name.pop((), None)
        return list_(_args), name
    else:
        return list_(name), {}


if __name__ == "__main__":
    import doctest
    doctest.testmod()
