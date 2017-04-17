# -*- coding: utf-8 -*-
"""
Midware is a general-purpose middleware library.

The purpose of middleware is to wrap user-defined handlers.
All middleware consists of two sections: `before` and `after`.
There is a special function that controls middleware execution order.
It threads a dictionary called `env` through the `before` sections
then calls the handler and then threads the handler's result
through `after` sections.
"""

from contextlib import contextmanager
import inspect

from .dict import assoc_in

"""
A global flag that controls printing debug information. 
"""
_verbose_mode = False


def identity(x):
    """
    A named identity function is nicer than `lambda x: x`.
    """
    return x


def compose(*funcs):
    """
    Returns a function that applies other functions in sequence.  
    `compose(f, g, h)(x, y)` is the same as `f(g(h(x, y)))`.
     
    If no arguments are provided, the identity function is returned.
    """
    if not funcs:
        return identity

    def wrapper(*args, **kwargs):
        fst, *rest = funcs
        ret = fst(*args, **kwargs)

        for f in rest:
            ret = f(ret)

        return ret

    return wrapper


def _print_inwards(middleware_name, hidden_mw=False):
    """
    Print a `middleware_name` with an inwards arrow
    if `_verbose_mode` is on and if middleware is not hidden.
    """
    if _verbose_mode and not hidden_mw:
        print('{}--->'.format(middleware_name))


def _print_outwards(middleware_name, hidden_mw=False):
    """
    Print a `middleware_name` with an outwards arrow
    if `_verbose_mode` is on and if middleware is not hidden.
    """
    if _verbose_mode and not hidden_mw:
        print('<---{}'.format(middleware_name))


def wrapper_from_contextmanager(cm, handler, ks=None):
    """
    Context managers and middleware wrappers have similar semantics,
    which makes converting context manager to a wrapper really easy.
    
    This function will be called from the body of a named middleware,
    so capturing this name needs to be done here. The wrapper itself will
    be called from elsewhere.
    """
    middleware_name = inspect.stack()[1][3]

    def wrapper(env):
        """
        Context manager is passed `env` as its only argument.
        The result of entering `cm` can be saved in `env`
        if the `ks` sequence of keys is specified.
        """
        _print_inwards(middleware_name, hasattr(cm, 'hidden_mw'))
        with cm(env) as v:
            if ks:
                assoc_in(env, ks, v)
            handled_env = handler(env)
        _print_outwards(middleware_name, hasattr(cm, 'hidden_mw'))

        return handled_env

    return wrapper


def wrapper_from_generator(g, handler, ks=None):
    """
    Generators with one `yield` statement are similar to
    context managers.

    Even though the code is the same just for `contextmanager(g)`
    instead of `cm`, it's not possible to reuse `wrapper_from_contextmanager`
    because `middleware_name` will be set to `wrapper_from_generator` (the caller).
    """
    middleware_name = inspect.stack()[1][3]

    def wrapper(env):
        _print_inwards(middleware_name, hasattr(g, 'hidden_mw'))
        with contextmanager(g)(env) as v:
            if ks:
                assoc_in(env, ks, v)
            handled_env = handler(env)
        _print_outwards(middleware_name, hasattr(g, 'hidden_mw'))

        return handled_env

    return wrapper


def _verbose(_):
    """
    This wrapper doesn't change the `env` passed to it. In its
    `before` section it turns `_verbose_mode` on and turns it off
    in the `after` section.
    """
    global _verbose_mode
    _verbose_mode = True
    yield
    _verbose_mode = False


def wrap_verbose(handler):
    """
    This middleware gets silently inserted into the collection
    of user-specified middleware, so it shouldn't be visible in
    debug output. To hide it `hidden_mw` attribute is set
    on the generator.
    """
    _verbose.hidden_mw = True
    return wrapper_from_generator(_verbose, handler)


def pipe_through(env, handler, *middleware, verbose=False):
    """
    This function kicks of the execution. The `env` is piped
    through `before` sections of `middleware` left to right
    and after the `handler` is executed the `env` is piped
    through `after` sections right to left.
    
    Setting `verbose` true inserts a hidden `wrap_verbose`
    middleware to the beginning.
    """
    middleware_ = list(middleware)
    if verbose:
        middleware_.insert(0, wrap_verbose)
    return compose(*reversed(middleware_))(handler)(env)


def exec_seq(handler, *middleware, verbose=False):
    """
    The same as `pipe_through`, but starts with an empty `env`.
    """
    return pipe_through({}, handler, *middleware, verbose=verbose)
