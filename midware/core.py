# -*- coding: utf-8 -*-

from contextlib import contextmanager
import inspect

_verbose_mode = False


def get_in(d, ks):
    *ks_, last = ks
    d_ = d

    for k in ks_:
        if k not in d_:
            return None
        d_ = d_[k]

    return d_.get(last)


def assoc_in(d, ks, v):
    *ks_, last = ks
    d_ = d

    for k in ks_:
        if k not in d_:
            d_[k] = {}
        d_ = d_[k]

    d_[last] = v
    return d


def dissoc_in(d, ks):
    *ks_, last = ks
    d_ = d

    for k in ks_:
        if k not in d_:
            return d
        d_ = d_[k]

    d_.pop(last, None)
    return d


def update(d, k, f, *args):
    d[k] = f(d[k], *args)
    return d


def update_in(d, ks, f, *args):
    v = f(get_in(d, ks), *args)
    assoc_in(d, ks, v)
    return d


def identity(x):
    return x


def compose(*funcs):
    if not funcs:
        return identity

    def wrapper(*args, **kwargs):
        fst, *rest = funcs
        ret = fst(*args, **kwargs)

        for f in rest:
            ret = f(ret)

        return ret

    return wrapper


def print_inwards(middleware_name, hidden_mw=False):
    if _verbose_mode and not hidden_mw:
        print('{}--->'.format(middleware_name))


def print_outwards(middleware_name, hidden_mw=False):
    if _verbose_mode and not hidden_mw:
        print('<---{}'.format(middleware_name))


def wrapper_from_contextmanager(cm, handler, ks=None):
    middleware_name = inspect.stack()[1][3]

    def wrapper(env):
        print_inwards(middleware_name, hasattr(cm, 'hidden_mw'))
        with cm(env) as v:
            if ks:
                assoc_in(env, ks, v)
            handled_env = handler(env)
        print_outwards(middleware_name, hasattr(cm, 'hidden_mw'))

        return handled_env

    return wrapper


def wrapper_from_generator(g, handler, ks=None):
    middleware_name = inspect.stack()[1][3]

    def wrapper(env):
        print_inwards(middleware_name, hasattr(g, 'hidden_mw'))
        with contextmanager(g)(env) as v:
            if ks:
                assoc_in(env, ks, v)
            handled_env = handler(env)
        print_outwards(middleware_name, hasattr(g, 'hidden_mw'))

        return handled_env

    return wrapper


def _verbose(_):
    global _verbose_mode
    _verbose_mode = True
    yield
    _verbose_mode = False


def verbose_wrapper(handler):
    _verbose.hidden_mw = True
    return wrapper_from_generator(_verbose, handler)


def through(env, handler, *wrappers, verbose=False):
    wrappers_ = list(wrappers)
    if verbose:
        wrappers_.insert(0, verbose_wrapper)
    return compose(*reversed(wrappers_))(handler)(env)


def clean_through(handler, *wrappers, verbose=False):
    return through({}, handler, *wrappers, verbose=verbose)


def inc(x):
    return x + 1


def dec(x):
    return x - 1


def no_op(_):
    yield


def wrap_no_op(handler):
    return wrapper_from_generator(no_op, handler)


def inc_n(env):
    yield
    update_in(env, ['n'], inc)


def wrap_inc_n(handler):
    return wrapper_from_generator(inc_n, handler)


def req(env):
    print('CTR')
    assoc_in(env, ['n'], 0)
    return env


print(clean_through(req, wrap_no_op, wrap_inc_n))
