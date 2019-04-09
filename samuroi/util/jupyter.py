from enum import Enum


class Runtime(Enum):
    JUPYTER = 'jupyter'
    TERMINAL = 'terminal'


def get_runtime() -> Runtime:
    try:
        from IPython import get_ipython
        try:
            ipy_str = str(type(get_ipython()))
            if 'zmqshell' in ipy_str:
                return Runtime.JUPYTER
            if 'terminal' in ipy_str:
                return 'ipython'
        except:
            return Runtime.TERMINAL
    except ImportError:
        return Runtime.TERMINAL


runtime = get_runtime()


def progress(iterable, **kwargs):
    """
    Print a progress bar while looping over iterable if running in Jupyter notebook and tqdm is available.
    :param iterable: The generator object to take from.
    :param kwargs: arguments passed to tqdm if available.
    :return: A generator with the same items, but wrapped into a progress display
    """
    if runtime is Runtime.JUPYTER:
        try:
            from tqdm import tqdm_notebook

            def wrap():
                for i in tqdm_notebook(iterable, **kwargs):
                    yield i

            return wrap()
        except ImportError:
            def wrap():
                for i in iterable:
                    yield i

            return wrap()
    else:
        def wrap():
            for i in iterable:
                yield i

        return wrap()
