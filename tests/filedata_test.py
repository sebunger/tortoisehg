import os
from nose.tools import *

from tortoisehg.hgqt import filedata, thgrepo

import helpers

def setup():
    global _tmpdir
    _tmpdir = helpers.mktmpdir(__name__)

    hg = helpers.HgClient(os.path.join(_tmpdir, 'status'))
    hg.init()
    hg.fwrite('.hg/hgrc', '[tortoisehg]\nmaxdiff = 1\n')  # 1kB

    hg.fwrite('text', 'foo\n')
    hg.fwrite('binary', '\0')
    hg.fwrite('text-over1kb', ('a' * 63 + '\n') * 16 + '\n')
    hg.commit('-Am', 'add')

    paths = ['text', 'binary', 'text-over1kb']
    for p in paths:
        hg.copy(p, p + '.copied')
    hg.commit('-m', 'copy')

    for p in paths:
        hg.rename(p, p + '.renamed')
    hg.commit('-m', 'rename')

def loaddata(reponame, rev, path, prev=None):
    # thgrepository extension is necessary because of repo.maxdiff
    repo = thgrepo.repository(path=os.path.join(_tmpdir, reponame))
    ctx = repo[rev]
    if prev is None:
        pctx = ctx.p1()
    else:
        pctx = repo[prev]
    fd = filedata.createFileData(ctx, pctx, path)
    fd.load()
    return fd


def check_error(fd, message):
    assert message in fd.error
    # no data should be loaded
    assert_false(fd.contents)
    assert_false(fd.olddata)
    assert_false(fd.diff)

def test_error_added():
    for rev, sfx in [(0, ''), (1, '.copied'), (2, '.renamed')]:
        for path, msg in [('binary', 'is binary'),
                          ('text-over1kb', 'is larger than')]:
            fd = loaddata('status', rev, path + sfx)
            yield check_error, fd, msg

def check_flabel(fd, message):
    assert message in fd.flabel

def test_flabel_added():
    for path in ['text', 'binary', 'text-over1kb']:
        for rev, sfx, msg in [(0, '', 'added'),
                              (1, '.copied', 'copied from'),
                              (2, '.renamed', 'renamed from')]:
            fd = loaddata('status', rev, path + sfx)
            yield check_flabel, fd, msg

def test_flabel_far_rename():
    fd = loaddata('status', 2, 'text.copied', 0)
    check_flabel(fd, 'renamed from')  # source 'text' is removed at rev 2
