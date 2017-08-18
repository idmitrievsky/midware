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
from inspect import isgeneratorfunction
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


def midware(name, ks, *args, **kwargs):
    """
    Generators with one `yield` statement are similar to
    context managers.

    Context managers and middleware wrappers have similar semantics,
    which makes converting context manager to a wrapper really easy.
    """

    def wrap_generator(g):
        def wrap_handler(handler):
            def wrapper(env):
                """
                Context manager is passed `env` as its only argument.
                The result of entering `cm` can be saved in `env`
                if the `ks` sequence of keys is specified.
                """
                _print_inwards(name, hasattr(g, 'hidden_mw'))

                cm_factory = contextmanager(fn) if isgeneratorfunction(
                    fn) else fn

                with cm_factory(env, *args, **kwargs) as ks:
                    if ks:
                        assoc_in(env, ks, v)
                    handled_env = handler(env)
                _print_outwards(name, hasattr(g, 'hidden_mw'))

                return handled_env

            return wrapper

        return wrap_handler

    return wrap_generator


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
