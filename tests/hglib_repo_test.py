"""Test for repository helper functions in hglib"""

import os
from nose.tools import *

from mercurial import hg
from tortoisehg.util import hglib

import helpers

def setup():
    global _tmpdir
    _tmpdir = helpers.mktmpdir(__name__)

    hg = helpers.HgClient(os.path.join(_tmpdir, 'empty'))
    hg.init()
    setup_repoid()

def openrepo(name):
    return hg.repository(hglib.loadui(), os.path.join(_tmpdir, name))


_repoidnodes = [
    '093f0fe4b6a9db9ad3537827ddb92c4dcf1406f9',
    '121d24cace2c5ed7211158e5eb4ad8ac4691f505',
    '0000000000000000000000000000000000000000',  # -1
    ]

def setup_repoid():
    for name in ['repoid-trivial', 'repoid-allhidden', 'repoid-rev0hidden']:
        hg = helpers.HgClient(os.path.join(_tmpdir, name))
        hg.init()
        # to use "hg debugobsolete" and suppress "obsolete feature not enabled"
        hg.fappend('.hg/hgrc', '[experimental]\nevolution.createmarkers = 1\n')
        hg.ftouch('foo')
        hg.commit('-Am0')
        hg.update('null')
        hg.ftouch('bar')
        hg.commit('-Am1')
        hg.update('null')
    hg = helpers.HgClient(os.path.join(_tmpdir, 'repoid-allhidden'))
    for n in _repoidnodes:
        hg.debugobsolete(n)
    hg = helpers.HgClient(os.path.join(_tmpdir, 'repoid-rev0hidden'))
    hg.debugobsolete(_repoidnodes[0])

def check_repoid(reponame, rootrev):
    repo = openrepo(reponame)
    nodehex = _repoidnodes[rootrev]
    assert_equal(nodehex[:12], hglib.shortrepoid(repo))
    assert_equal(nodehex.decode('hex'), hglib.repoidnode(repo))

def test_repoid():
    for reponame, rev in [('empty', -1),
                          ('repoid-trivial', 0),
                          ('repoid-allhidden', -1),
                          ('repoid-rev0hidden', 1)]:
        yield check_repoid, reponame, rev
