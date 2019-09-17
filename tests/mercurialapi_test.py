"""Test for compatibility with Mercurial API"""

import inspect
from nose.tools import *

from tortoisehg.util import hglib, pipeui

def assert_same_argspec(f, g):
    fa, ga = inspect.getargspec(f), inspect.getargspec(g)
    assert_equals(fa, ga,
                  '%s != %s' % (inspect.formatargspec(*fa),
                                inspect.formatargspec(*ga)))

def overridden_methods(cls):
    basemethods = inspect.getmembers(cls.__base__, inspect.ismethod)
    return [(name, basemeth, getattr(cls, name))
            for name, basemeth in basemethods
            if basemeth.__func__ is not getattr(cls, name).__func__]


def test_pipeui():
    ui = hglib.loadui()
    pipeui.uisetup(ui)
    for name, basemeth, meth in overridden_methods(ui.__class__):
        yield assert_same_argspec, basemeth, meth
