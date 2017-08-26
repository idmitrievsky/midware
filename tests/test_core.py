# -*- coding: utf-8 -*-

import pytest

import midware.core as core


@pytest.fixture
def nested_dict():
    return {'a': {'b': 0}, 'c': 1}


def test_get_in(nested_dict):
    assert core.get_in(nested_dict, ('a')) == {'b': 0}
    assert core.get_in(nested_dict, ('a', 'b')) == 0
    assert core.get_in(nested_dict, ('c')) == 1

    assert core.get_in(nested_dict, ('a', 'd')) == None
    assert core.get_in(nested_dict, ('d')) == None


def test_get_in_default(nested_dict):
    assert core.get_in(nested_dict, ('a', 'b')) == 0

    assert core.get_in(nested_dict, ('c', 'd')) == None
    assert core.get_in(nested_dict, ('a', 'd')) == None
    assert core.get_in(nested_dict, ('a', 'd'), default=0) == 0


def test_assoc_in():
    d = {}

    core.assoc_in(d, ('a'), 0)
    assert d['a'] == 0

    with pytest.raises(TypeError):
        core.assoc_in(d, ('a', 'b'), 0)

    core.assoc_in(d, ('b', 'c'), 1)
    assert d['b']['c'] == 1


def test_identity():
    assert core.identity(1) == 1
    assert core.identity('a') == 'a'
    assert core.identity(None) == None


def add_two(x):
    return x + 2


def add_three(x):
    return x + 3


def test_compose():
    assert core.compose(add_two, add_three)(1) == 6


def test_compose_order():
    assert core.compose(sum, add_two, add_three)([1, 2, 3]) == 11


@pytest.fixture
def verbose(scope='function'):
    core._VERBOSE_MODE = True
    yield
    core._VERBOSE_MODE = False


def test_print_inwards(verbose, capsys):
    core._print_inwards('abc')
    out, err = capsys.readouterr()
    assert out == 'abc--->\n'
    assert err == ''


def test_print_outwards(verbose, capsys):
    core._print_outwards('xyz')
    out, err = capsys.readouterr()
    assert out == '<---xyz\n'
    assert err == ''


import os.path as fs


def test_mw_from_cm_enter(tmpdir):
    tmpfile = fs.join(tmpdir, 'tmp.txt')
    with open(tmpfile, 'w') as f:
        print('abc', file=f)

    ks = ('file', 'desc')
    mw = core.mw_from_cm('test_mw', open, ks, {}, file=tmpfile)

    lines = None

    def handler(ctx):
        with core.get_in(ctx, ks) as f:
            assert f.readlines() == ['abc\n']

        return ctx

    ctx = mw(handler)({})


def test_mw_from_cm_exit(tmpdir):
    tmpfile = fs.join(tmpdir, 'tmp.txt')
    with open(tmpfile, 'w') as f:
        print('abc', file=f)

    ks = ('file', 'desc')
    mw = core.mw_from_cm('test_mw', open, ks, {}, file=tmpfile)

    ctx = mw(core.identity)({})

    with pytest.raises(ValueError):
        with core.get_in(ctx, ks) as f:
            f.readlines()


def test_mw_from_cm_exit(tmpdir, verbose, capsys):
    tmpfile = fs.join(tmpdir, 'tmp.txt')
    with open(tmpfile, 'w') as f:
        print('abc', file=f)

    ks = ('file', 'desc')
    mw = core.mw_from_cm('test_cm_mw', open, ks, {}, file=tmpfile)

    ctx = mw(core.identity)({})

    out, err = capsys.readouterr()
    assert out == 'test_cm_mw--->\n<---test_cm_mw\n'
    assert err == ''


@core.middleware('wrap_add')
def wrap_add(ctx):
    amount = ctx['amount']
    ctx['value'] += amount

    new_ctx = yield ctx

    new_ctx['post'] = True

    yield new_ctx


def test_middleware():
    def add_one(ctx):
        ctx['value'] += 1
        return ctx

    ctx = wrap_add(add_one)({'value': 1, 'amount': 2})

    assert ctx['value'] == 4
    assert ctx['post']


def test_middleware_verbose(verbose, capsys):
    ctx = wrap_add(core.identity)({'value': 1, 'amount': 2})

    assert ctx['value'] == 3
    assert ctx['post']

    out, err = capsys.readouterr()
    assert out == 'wrap_add--->\n<---wrap_add\n'
    assert err == ''


@core.middleware('wrap_sub', 1)
def wrap_sub(ctx, amount):
    ctx['value'] -= amount

    new_ctx = yield ctx

    yield new_ctx


def test_middleware_args():
    ctx = wrap_sub(core.identity)({'value': 1})

    assert ctx['value'] == 0


@core.middleware('wrap_replace')
def wrap_replace(ctx):
    _ = yield ctx

    yield {'replacement': True}


def test_middleware_replacement():
    ctx = wrap_add(wrap_replace(core.identity))({'value': 1, 'amount': 2})

    assert ctx == {'replacement': True, 'post': True}


def wrap_unnamed(handle):
    def new_handle(ctx):
        new_ctx = handle(ctx)
        return new_ctx

    return new_handle


def test_unnamed_verbose(verbose, capsys):
    ctx = wrap_unnamed(core.identity)({})

    out, err = capsys.readouterr()
    assert out == ''
    assert err == ''


@core.named('wrap_named')
def wrap_named(handle):
    def new_handle(ctx):
        new_ctx = handle(ctx)
        return new_ctx

    return new_handle


def test_named_verbose(verbose, capsys):
    ctx = wrap_named(core.identity)({})

    out, err = capsys.readouterr()
    assert out == 'wrap_named--->\n<---wrap_named\n'
    assert err == ''
