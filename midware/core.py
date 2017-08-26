# -*- coding: utf-8 -*-
"""
Middleware can always be defined in this straightforward manner:

    def wrap_smth(handler):
        def new_handler(ctx):
            # do smth with ctx
            # prime it with some values
            new_ctx = handler(ctx)
            # do some post-processing with new_ctx
            return new_ctx

        return handler

The first indentation level is not really necessary.
Also, wrapping a handlers into a lot of middleware layers
requires a lot of unnecessary brackets.

This module provides means to work with middleware in a more convinient way.

Since context is usually a nested `dict`, functions `midware.core.get_in` and
`midware.core.assoc_in` are provided for easier manipulation of values.

For no-op handlers and middleware there is `midware.core.identity`.

`midware.core.compose` allows for piping functions while not using any brackets,
but `midware.core.wrap_and_call` is suited specifically for the most
frequent one-handler-many-layers use case.

The function called `midware.core.middleware` turns generators into middleware. With
this function the previous example turns into:

    @midware.core.middleware('wrap_smth')
    def wrap_smth(ctx):
        # do smth with ctx
        # prime it with some values
        new_ctx = yield ctx
        # do some post-processing with new_ctx
        yield new_ctx

Here `'wrap_smth'` stands for the name of the middleware and it's used when
middleware is layered with `midware.core.wrap_and_call` and `verbose` is passed as `True`.
If middleware is defined without the usage of generators, then the name can be set
using `midware.core.named`. Again the following is better than the first example:

    @midware.core.named('wrap_smth')
    def wrap_smth(handler):
        def new_handler(ctx):
            # do smth with ctx
            # prime it with some values
            new_ctx = handler(ctx)
            # do some post-processing with new_ctx
            return new_ctx

        return handler
"""

_VERBOSE_MODE = False


def get_in(d, ks, default=None):
    """
    Returns a value in a nested associative structure,
    where `ks` is a sequence of keys. Returns `None`, if the key
    is not present, or the `default` value, if supplied.
    """
    *ks_, last = ks
    d_ = d

    for k in ks_:
        if type(d_) != dict or k not in d_:
            return default
        d_ = d_[k]

    if type(d_) == dict:
        return d_.get(last, default)

    return default


def assoc_in(d, ks, v):
    """
    Associates a value in a nested associative structure, where `ks` is a
    sequence of keys and `v` is the new value, and returns a nested structure.
    If any levels do not exist, `dict`s will be created.
    """
    *ks_, last = ks
    d_ = d

    for k in ks_:
        if k not in d_:
            d_[k] = {}
        d_ = d_[k]

    d_[last] = v
    return d


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


def _print_inwards(middleware_name):
    """
    Print a `middleware_name` with a right arrow
    if `_VERBOSE_MODE` is on.
    """
    if _VERBOSE_MODE:
        print('{}--->'.format(middleware_name))


def _print_outwards(middleware_name):
    """
    Print a `middleware_name` with a left arrow
    if `_VERBOSE_MODE` is on.
    """
    if _VERBOSE_MODE:
        print('<---{}'.format(middleware_name))


def mw_from_cm(name, cm_constructor, ks=None, ctx_args={}, **kwargs):
    """
    This function is not very useful, so it's advised not to use it, because
    it can be removed at any time before 1.0.0
    """

    def new_middleware(handler):
        def new_handler(ctx):
            _print_inwards(name)

            ctx_kwargs = {}
            for k, ks_ in ctx_args:
                ctx_kwargs[k] = get_in(ctx, ks_)

            with cm_constructor(**ctx_kwargs, **kwargs) as v:
                if ks:
                    assoc_in(ctx, ks, v)
                new_ctx = handler(ctx)

            _print_outwards(name)

            return new_ctx

        return new_handler

    return new_middleware


def middleware(name, *args, **kwargs):
    """
    This function is used to decorate generators with exactly two `yield` statements
    and turn them into middleware. For examples see documentation to this module and tests.

    Extra arguments beyond name are passed to the generator that is being decorated during
    instantiation. If they are not defined during interpretation of this module, then this
    function can be used as a regular callable and not as an annotation.
    """

    def new_annotate(g_fn):
        def new_middleware(handler):
            def new_handler(ctx):
                _print_inwards(name)

                g = g_fn(ctx, *args, **kwargs)

                changed_ctx = next(g)
                new_ctx = handler(changed_ctx)
                last_ctx = g.send(new_ctx)

                _print_outwards(name)

                return last_ctx

            return new_handler

        return new_middleware

    return new_annotate


def named(name):
    """
    This function is used to decorate middleware functions in order
    for their before and after sections to show up during a verbose run.
    For examples see documentation to this module and tests.
    """

    def new_annotate(mware):
        def new_middleware(handler):

            new_handler = mware(handler)

            def verbose_handler(ctx):
                _print_inwards(name)

                new_ctx = new_handler(ctx)

                _print_outwards(name)

                return new_ctx

            return verbose_handler

        return new_middleware

    return new_annotate


def wrap_and_call(ctx, handler, *middleware, verbose=False):
    """
    This function layers `middleware` left to right around
    the `handler` and calls it all with `ctx` as an argument.
    
    Setting `verbose` to `True` prints when handlers start their
    before and after sections.
    """
    global _VERBOSE_MODE
    _VERBOSE_MODE = verbose

    middleware_ = list(middleware)

    return compose(*reversed(middleware_))(handler)(ctx)
