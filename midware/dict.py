# -*- coding: utf-8 -*-
"""
This module contains convenient clojure-style operations on dicts.
"""


def get_in(d, ks, default=None):
    """
    Returns a value in a nested associative structure,
    where `ks` is a sequence of keys. Returns `None` if the key
    is not present, or the `default` value if supplied.
    """
    *ks_, last = ks
    d_ = d

    for k in ks_:
        if k not in d_:
            return default
        d_ = d_[k]

    return d_.get(last, default)


def pairs(iterable):
    """
    Turns `a, b, c, d` into `(a, b), (c, d)`.
    """
    fst_iter, snd_iter = [iter(iterable)] * 2
    while True:
        yield (next(fst_iter), next(snd_iter))


def assoc(d, *kvs):
    """
    Returns a dict, that contains the mapping of keys to vals. 
    """
    for k, v in pairs(kvs):
        d[k] = v

    return d


def assoc_in(d, ks, v):
    """
    Associates a value in a nested associative structure, where `ks` is a
    sequence of keys and `v` is the new value and returns a nested structure.
    If any levels do not exist, dicts will be created.
    """
    *ks_, last = ks
    d_ = d

    for k in ks_:
        if k not in d_:
            d_[k] = {}
        d_ = d_[k]

    d_[last] = v
    return d


def dissoc(d, *ks):
    """
    Returns a dict, that does not contain a mapping for keys.
    """
    for k in ks:
        d.pop(k, None)

    return d


def dissoc_in(d, ks):
    """
    Returns a dict, that does not contain a nested mapping, where `ks` is a
    sequence of keys.
    """
    *ks_, last = ks
    d_ = d

    for k in ks_:
        if k not in d_:
            return d
        d_ = d_[k]

    d_.pop(last, None)
    return d


def update(d, k, f, *args):
    """
    Updates a value in an associative structure, where `k` is a
    key and `f` is a function that will take the old value
    and any supplied `args` and return the new value, and returns a structure.
    If the key does not exist, `None` is passed as the old value.
    """
    v = None if k not in d else d[k]
    d[k] = f(v, *args)
    return d


def update_in(d, ks, f, *args):
    """
    Updates a value in a nested associative structure, where `ks` is a
    sequence of keys and `f` is a function that will take the old value
    and any supplied `args` and return the new value, and returns a nested
    structure. If any levels do not exist, dicts will be created.
    """
    new_v = f(get_in(d, ks), *args)
    assoc_in(d, ks, new_v)
    return d
