from __future__ import absolute_import

import mock
import os
import sys
import unittest

from mercurial import (
    pycompat,
)

from nose.plugins.skip import SkipTest

from tortoisehg.hgqt.qtcore import (
    QModelIndex,
    Qt,
)
from tortoisehg.hgqt.qtgui import (
    QApplication,
)

from tortoisehg.util import patchctx
from tortoisehg.hgqt import (
    thgrepo,
)
from tortoisehg.hgqt.manifestmodel import ManifestModel

import helpers

def setup():
    # necessary for style().standardIcon()
    if not isinstance(QApplication.instance(), QApplication):
        raise SkipTest

    global _tmpdir
    _tmpdir = helpers.mktmpdir(__name__)

def alldata(model, parent=QModelIndex()):
    return [model.data(model.index(r, 0, parent))
            for r in pycompat.xrange(model.rowCount(parent))]


class ManifestModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hg = hg = helpers.HgClient(os.path.join(_tmpdir, cls.__name__))
        hg.init()
        hg.ftouch('foo', 'bar', 'baz/bax', 'baz/box')
        hg.addremove()
        hg.commit('-m', 'foobar')

        hg.fwrite('bar', 'hello\n')
        hg.remove('baz/box')
        hg.ftouch('zzz')
        hg.addremove()
        hg.commit('-m', 'remove baz/box, add zzz, modify bar')

        hg.clone('-U', '.', 'sub')
        hg.fappend('.hgsub', 'sub = sub\n')
        hg.commit('-Am', 'add empty sub')

        hg.update('-R', 'sub', '1')
        hg.commit('-Am', 'update sub')

        os.makedirs(hg.wjoin(b'deep'))
        hg.clone('-r0', '.', 'deep/sub')
        hg.fappend('.hgsub', 'deep/sub = deep/sub\n')
        hg.commit('-m', 'add deep/sub')

        hg.clone('-r0', '.', 'sub/nested')
        hg.fappend('sub/.hgsub', 'nested = nested')
        hg.addremove('-R', 'sub')
        hg.commit('-Sm', 'add sub/nested')

        hg.fappend('sub/bar', 'hello2\n')
        hg.commit('-Sm', 'modify sub/bar')

        hg.fwrite('.hgsub', 'deep/sub = deep/sub\n')
        hg.commit('-m', 'remove sub')

        hg.fappend('bar', 'hello3\n')
        hg.commit('-m', 'modify bar')

        hg.update('4')
        hg.fappend('foo', 'hello3\n')
        hg.fappend('bar', 'hello4\n')
        hg.commit('-m', 'modify foo and bar (new head)')

        hg.merge('--tool=internal:local')
        hg.commit('-m', 'merge (take local bar)')

        hg.branch('stable')
        hg.commit('-m', 'new branch stable (empty commit)')

    def setUp(self):
        repo = thgrepo.repository(path=self.hg.path)
        self.repoagent = thgrepo.RepoAgent(repo)

    def new_unpopulated_model(self, rev):
        m = ManifestModel(self.repoagent, rev=rev)
        return m

    def new_model(self, rev):
        m = self.new_unpopulated_model(rev)
        m.fetchMore(QModelIndex())
        return m

    def test_data(self):
        m = self.new_model(0)
        self.assertEqual('bar', m.data(m.index(1, 0)))
        self.assertEqual('baz', m.data(m.index(0, 0)))
        self.assertEqual('foo', m.data(m.index(2, 0)))

    def test_data_subdir(self):
        m = self.new_model(0)
        self.assertEqual('bax', m.data(m.index(0, 0, m.index(0, 0))))
        self.assertEqual('box', m.data(m.index(1, 0, m.index(0, 0))))

    def test_data_inexistent(self):
        m = self.new_model(0)
        self.assertEqual(None, m.data(QModelIndex()))
        self.assertEqual(None, m.data(m.index(0, 0, m.index(1, 0))))

    def test_data_subrepo(self):
        m = self.new_model(3)
        self.assertEqual(['baz', 'sub', '.hgsub'],  alldata(m)[:3])
        self.assertEqual(['baz', 'bar', 'foo', 'zzz'],
                         alldata(m, m.indexFromPath('sub')))

    def test_data_empty_subrepo(self):
        m = self.new_model(2)
        self.assertEqual(['baz', 'sub', '.hgsub'],  alldata(m)[:3])

    def test_data_deep_subrepo(self):
        m = self.new_model(4)
        self.assertEqual(['sub'], alldata(m, m.indexFromPath('deep')))
        self.assertEqual(['baz', 'bar', 'foo'],
                         alldata(m, m.indexFromPath('deep/sub')))

    def test_data_nested_subrepo(self):
        m = self.new_model(5)
        self.assertEqual(['baz', 'nested', '.hgsub'],
                         alldata(m, m.indexFromPath('sub'))[:3])
        self.assertEqual(['baz', 'bar', 'foo'],
                         alldata(m, m.indexFromPath('sub/nested')))

    def test_flat_data(self):
        m = self.new_model(0)
        m.setFlat(True)
        self.assertEqual(['bar', 'baz/bax', 'baz/box', 'foo'], alldata(m))

    def test_flat_data_subrepo(self):
        m = self.new_model(3)
        m.setFlat(True)
        self.assertEqual(['sub', '.hgsub', '.hgsubstate', 'bar', 'baz/bax'],
                         alldata(m)[:5])

    def test_drag_flag(self):
        m = self.new_model(0)
        # only files are drag enabled
        self.assertTrue(m.flags(m.indexFromPath('foo')) & Qt.ItemIsDragEnabled)
        self.assertFalse(m.flags(m.indexFromPath('baz')) & Qt.ItemIsDragEnabled)

    def test_isdir(self):
        m = self.new_model(3)
        self.assertTrue(m.isDir(m.indexFromPath('')))
        self.assertTrue(m.isDir(m.indexFromPath('baz')))
        self.assertFalse(m.isDir(m.indexFromPath('foo')))
        self.assertTrue(m.isDir(m.indexFromPath('sub')))
        self.assertFalse(m.isDir(m.indexFromPath('sub/foo')))
        self.assertTrue(m.isDir(m.indexFromPath('sub/baz')))

    def test_flat_isdir_subrepo(self):
        m = self.new_model(3)
        m.setFlat(True)
        self.assertTrue(m.isDir(m.indexFromPath('sub')))

    def test_rawfctx(self):
        m = self.new_model(5)
        self.check_rawfctx(m, 'foo', (5, '', 'foo'))
        self.check_rawfctx(m, 'sub', (5, '', 'sub'))
        self.check_rawfctx(m, 'sub/foo', (2, 'sub', 'foo'))
        self.check_rawfctx(m, 'sub/baz/bax', (2, 'sub', 'baz/bax'))
        self.check_rawfctx(m, 'sub/invalid', (-1, '', ''))
        self.check_rawfctx(m, 'deep/sub/foo', (0, 'deep/sub', 'foo'))
        self.check_rawfctx(m, 'sub/nested', (2, 'sub', 'nested'))
        self.check_rawfctx(m, 'sub/nested/foo', (0, 'sub/nested', 'foo'))

    def check_rawfctx(self, m, path, expected):
        fd = m.fileData(m.indexFromPath(path))
        self.assertEqual(expected,
                         (fd.rev(), fd.repoRootPath(), fd.canonicalFilePath()))

    def test_null_filedata(self):
        m = self.new_model(0)
        fd = m.fileData(QModelIndex())
        self.assertTrue(fd.isNull())
        self.assertFalse(fd.isValid())

    def test_rowcount(self):
        m = self.new_model(0)
        self.assertEqual(3, m.rowCount())

    def test_rowcount_subdirs(self):
        m = self.new_model(0)
        self.assertEqual(2, m.rowCount(m.index(0, 0)))

    def test_rowcount_invalid(self):
        m = self.new_model(0)
        self.assertEqual(0, m.rowCount(m.index(1, 0)))

    def test_pathfromindex(self):
        m = self.new_model(0)
        self.assertEqual('', m.filePath(QModelIndex()))
        self.assertEqual('bar', m.filePath(m.index(1, 0)))
        self.assertEqual('baz', m.filePath(m.index(0, 0)))
        self.assertEqual('baz/bax', m.filePath(m.index(0, 0, m.index(0, 0))))

    def test_indexfrompath(self):
        m = self.new_model(0)
        self.assertEqual(QModelIndex(), m.indexFromPath(''))
        self.assertEqual(m.index(1, 0), m.indexFromPath('bar'))
        self.assertEqual(m.index(0, 0), m.indexFromPath('baz'))
        self.assertEqual(m.index(0, 0, m.index(0, 0)),
                         m.indexFromPath('baz/bax'))

    def test_flat_indexfrompath(self):
        m = self.new_model(0)
        m.setFlat(True)
        self.assertEqual(m.index(0, 0), m.indexFromPath('bar'))
        self.assertFalse(m.indexFromPath('baz').isValid())
        self.assertEqual(m.index(1, 0), m.indexFromPath('baz/bax'))

    def test_subrepotype(self):
        m = self.new_model(5)
        self.assertEqual('hg', m.subrepoType(m.indexFromPath('sub')))
        self.assertEqual('hg', m.subrepoType(m.indexFromPath('deep/sub')))
        self.assertEqual('hg', m.subrepoType(m.indexFromPath('sub/nested')))
        self.assertEqual(None, m.subrepoType(m.indexFromPath('foo')))

    def test_removed_should_be_listed(self):
        m = self.new_model(1)
        m.setStatusFilter('MARC')
        self.assertTrue(m.indexFromPath('baz/box').isValid())

    def test_removed_subrepo(self):
        m = self.new_model(7)
        m.setStatusFilter('MARCS')
        self.assertTrue(m.indexFromPath('sub').isValid())
        self.assertEqual('R', m.subrepoStatus(m.indexFromPath('sub')))
        self.assertEqual('hg', m.subrepoType(m.indexFromPath('sub')))

    def test_status_role(self):
        m = self.new_model(0)
        self.assertEqual('A', m.data(m.indexFromPath('foo'),
                                     role=ManifestModel.StatusRole))

        m = self.new_model(1)
        m.setStatusFilter('MARC')
        self.assertEqual('C', m.data(m.indexFromPath('foo'),
                                     role=ManifestModel.StatusRole))
        self.assertEqual('R', m.data(m.indexFromPath('baz/box'),
                                     role=ManifestModel.StatusRole))

        m = self.new_model(2)
        self.assertEqual('S', m.data(m.indexFromPath('sub'),
                                     role=ManifestModel.StatusRole))

    def test_status_role_invalid(self):
        m = self.new_model(0)
        self.assertEqual(None, m.data(QModelIndex(),
                                      role=ManifestModel.StatusRole))

    def test_status_in_subrepo(self):
        # it should show changes from the parent revision of the _main_ repo,
        # not the parent of the sub repo itself
        m = self.new_model(3)
        self.assertEqual('A', m.fileStatus(m.indexFromPath('sub/foo')))
        self.assertEqual('A', m.fileStatus(m.indexFromPath('sub/bar')))
        m = self.new_model(4)
        self.assertEqual('C', m.fileStatus(m.indexFromPath('sub/foo')))
        self.assertEqual('C', m.fileStatus(m.indexFromPath('sub/bar')))
        m = self.new_model(6)
        self.assertEqual('C', m.fileStatus(m.indexFromPath('sub/foo')))
        self.assertEqual('M', m.fileStatus(m.indexFromPath('sub/bar')))

    def test_subrepo_status(self):
        m = self.new_model(2)
        self.assertEqual('A', m.subrepoStatus(m.indexFromPath('sub')))
        m = self.new_model(3)
        self.assertEqual('M', m.subrepoStatus(m.indexFromPath('sub')))
        m = self.new_model(4)
        self.assertEqual('C', m.subrepoStatus(m.indexFromPath('sub')))

    def test_subrepo_rev(self):
        m = self.new_model(2)
        self.assertEqual(-1, m.rev(m.indexFromPath('sub')))
        self.assertEqual(-1, m.baseRev(m.indexFromPath('sub')))
        m = self.new_model(3)
        self.assertEqual(1, m.rev(m.indexFromPath('sub')))
        self.assertEqual(-1, m.baseRev(m.indexFromPath('sub')))
        m = self.new_model(4)
        self.assertEqual(1, m.baseRev(m.indexFromPath('sub')))

    def test_status_filter_modified(self):
        m = self.new_model(1)
        m.setStatusFilter('M')
        self.assertNotEqual(QModelIndex(), m.indexFromPath('bar'))  # modified
        self.assertEqual(QModelIndex(), m.indexFromPath('zzz'))  # added
        self.assertEqual(QModelIndex(), m.indexFromPath('baz/box'))  # removed
        self.assertEqual(QModelIndex(), m.indexFromPath('foo'))  # clean

    def test_status_filter_added(self):
        m = self.new_model(1)
        m.setStatusFilter('A')
        self.assertEqual(QModelIndex(), m.indexFromPath('bar'))  # modified
        self.assertNotEqual(QModelIndex(), m.indexFromPath('zzz'))  # added
        self.assertEqual(QModelIndex(), m.indexFromPath('baz/box'))  # removed
        self.assertEqual(QModelIndex(), m.indexFromPath('foo'))  # clean

    def test_status_filter_removed(self):
        m = self.new_model(1)
        m.setStatusFilter('R')
        self.assertEqual(QModelIndex(), m.indexFromPath('bar'))  # modified
        self.assertEqual(QModelIndex(), m.indexFromPath('zzz'))  # added
        self.assertNotEqual(QModelIndex(), m.indexFromPath('baz/box'))  # removed
        self.assertEqual(QModelIndex(), m.indexFromPath('foo'))  # clean

    def test_status_filter_clean(self):
        m = self.new_model(1)
        m.setStatusFilter('C')
        self.assertEqual(QModelIndex(), m.indexFromPath('bar'))  # modified
        self.assertEqual(QModelIndex(), m.indexFromPath('zzz'))  # added
        self.assertEqual(QModelIndex(), m.indexFromPath('baz/box'))  # removed
        self.assertNotEqual(QModelIndex(), m.indexFromPath('foo'))  # clean

    def test_status_filter_change(self):
        m = self.new_model(1)
        m.setStatusFilter('C')
        self.assertEqual(QModelIndex(), m.indexFromPath('bar'))  # modified
        self.assertNotEqual(QModelIndex(), m.indexFromPath('foo'))  # clean

        m.setStatusFilter('M')
        self.assertNotEqual(QModelIndex(), m.indexFromPath('bar'))  # modified
        self.assertEqual(QModelIndex(), m.indexFromPath('foo'))  # clean

    def test_status_filter_empty_subrepo(self):
        m = self.new_model(2)
        m.setStatusFilter('AS')
        self.assertTrue(m.indexFromPath('sub').isValid())

    def test_status_filter_deep_subrepo(self):
        m = self.new_model(4)
        m.setStatusFilter('AS')
        self.assertTrue(m.indexFromPath('deep/sub').isValid())
        m.setStatusFilter('CS')
        self.assertFalse(m.indexFromPath('deep/sub').isValid())

    def test_status_filter_nested_subrepo(self):
        m = self.new_model(5)
        # 'sub' is M, but 'sub/bar', etc. are C
        m.setStatusFilter('CS')
        self.assertTrue(m.indexFromPath('sub').isValid())
        self.assertFalse(m.indexFromPath('sub/nested').isValid())
        # 'sub' is M, but 'sub/nested' is A
        m.setStatusFilter('AS')
        self.assertTrue(m.indexFromPath('sub').isValid())
        self.assertTrue(m.indexFromPath('sub/nested').isValid())

    def test_status_filter_multi(self):
        m = self.new_model(1)
        m.setStatusFilter('MC')
        self.assertNotEqual(QModelIndex(), m.indexFromPath('bar'))  # modified
        self.assertEqual(QModelIndex(), m.indexFromPath('zzz'))  # added
        self.assertEqual(QModelIndex(), m.indexFromPath('baz/box'))  # removed
        self.assertNotEqual(QModelIndex(), m.indexFromPath('foo'))  # clean

    def test_name_filter(self):
        m = self.new_model(0)
        m.setNameFilter('ax')
        self.assertFalse(m.indexFromPath('bar').isValid())
        self.assertTrue(m.indexFromPath('baz/bax').isValid())
        self.assertFalse(m.indexFromPath('baz/box').isValid())
        self.assertFalse(m.indexFromPath('foo').isValid())

    def test_name_filter_glob(self):
        m = self.new_model(0)
        m.setNameFilter('b*x')
        self.assertFalse(m.indexFromPath('bar').isValid())
        self.assertTrue(m.indexFromPath('baz/bax').isValid())
        self.assertTrue(m.indexFromPath('baz/box').isValid())
        self.assertFalse(m.indexFromPath('foo').isValid())

    def test_name_filter_fileset(self):
        m = self.new_model(0)
        m.setNameFilter('relpath:foo')
        self.assertFalse(m.indexFromPath('bar').isValid())
        self.assertTrue(m.indexFromPath('foo').isValid())

    def test_name_filter_invalid_path(self):
        m = self.new_model(0)
        m.setNameFilter('relpath:/foo')  # no "Abort: /foo not under root"
        self.assertEqual(0, m.rowCount())

    def test_name_filter_unparsable(self):
        m = self.new_model(0)
        m.setNameFilter('set:invalid_query(')  # no ParseError
        self.assertEqual(0, m.rowCount())

    def test_name_filter_subrepo(self):
        m = self.new_model(3)
        m.setNameFilter('ba*')
        self.assertFalse(m.indexFromPath('sub/foo').isValid())
        self.assertTrue(m.indexFromPath('sub/bar').isValid())
        self.assertTrue(m.indexFromPath('sub/baz/bax').isValid())

    def test_name_filter_empty_subrepo(self):
        m = self.new_model(2)
        m.setNameFilter('sub')
        self.assertTrue(m.indexFromPath('sub').isValid())
        m.setNameFilter('foo')
        self.assertFalse(m.indexFromPath('sub').isValid())

    def test_changedfiles_filter_merge(self):
        m = self.new_model(10)
        m.setStatusFilter('MARS')
        self.assertEqual(['sub', '.hgsub', '.hgsubstate', 'bar'], alldata(m))
        m.setChangedFilesOnly(True)
        self.assertEqual(['bar'], alldata(m))

    def test_changedfiles_filter_emptycommit(self):
        m = self.new_model(11)
        self.assertTrue(m.rowCount() > 0)
        m.setChangedFilesOnly(True)
        self.assertEqual(0, m.rowCount())

    def test_change_rev(self):
        m = self.new_model(-1)
        self.assertEqual(-1, m.rev())
        m.setRev(0)
        self.assertEqual(0, m.rev())
        self.assertEqual(['baz', 'bar', 'foo'], alldata(m))

    def test_change_rev_unpopulated(self):
        m = self.new_unpopulated_model(0)
        self.assertTrue(m.canFetchMore(QModelIndex()))
        m.setRev(1)
        self.assertEqual(1, m.rev())
        self.assertTrue(m.canFetchMore(QModelIndex()))

    def test_change_rev_by_ctx(self):
        repo = self.repoagent.rawRepo()
        m = self.new_model(0)
        m.setRawContext(repo[1])
        self.assertEqual(1, m.rev())
        # should not fall back to patch handler
        self.assertTrue(m.flags(m.indexFromPath('foo')) & Qt.ItemIsDragEnabled)

    def test_change_base_rev(self):
        m = self.new_model(10)
        m.setStatusFilter('MARS')
        self.assertEqual(9, m.baseRev())
        m.setRev(10, m.SecondParent)
        self.assertEqual(8, m.baseRev())
        self.assertEqual(['bar', 'foo'], alldata(m))
        m.setRev(10, 4)
        self.assertEqual(['sub', '.hgsub', '.hgsubstate', 'bar', 'foo'],
                         alldata(m))

    def test_rev_loaded_on_initial_population(self):
        m = self.new_unpopulated_model(0)
        loaded = mock.Mock()
        m.revLoaded.connect(loaded)
        m.setRev(1)
        self.assertFalse(loaded.called, 'not populated but loaded emitted')
        m.fetchMore(QModelIndex())
        loaded.assert_called_once_with(1)

    def test_rev_loaded_on_change(self):
        m = self.new_model(0)
        loaded = mock.Mock()
        m.revLoaded.connect(loaded)
        m.setRev(1)
        loaded.assert_called_once_with(1)

    def test_no_rev_loaded_on_filter_change(self):
        m = self.new_model(0)
        loaded = mock.Mock()
        m.revLoaded.connect(loaded)
        m.setNameFilter('foo')
        self.assertFalse(loaded.called)

    def test_change_flat_unpopulated(self):
        m = self.new_unpopulated_model(0)
        self.assertTrue(m.canFetchMore(QModelIndex()))
        m.setFlat(True)
        self.assertTrue(m.isFlat())
        self.assertTrue(m.canFetchMore(QModelIndex()))


class ManifestModelPatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hg = hg = helpers.HgClient(os.path.join(_tmpdir, cls.__name__))
        hg.init()
        hg.ftouch('foo', 'bar/baz')
        # patchctx can't detect status without content
        hg.fwrite('foo', 'hello1\n')
        hg.fwrite('bar/baz', 'hello2\n')
        hg.addremove()
        hg.qnew('patch0.diff')

        hg.fappend('foo', 'hello3\n')
        hg.remove('bar/baz')
        hg.qnew('patch1.diff')

        hg.qpop('-a')

    def setUp(self):
        repo = thgrepo.repository(path=self.hg.path)
        self.repoagent = thgrepo.RepoAgent(repo)

    def new_model(self, patch):
        m = ManifestModel(self.repoagent)
        repo = self.repoagent.rawRepo()
        m.setRawContext(repo[patch])
        m.fetchMore(QModelIndex())
        return m

    def test_data(self):
        m = self.new_model('patch0.diff')
        self.assertEqual(['bar', 'foo'], alldata(m))

    def test_no_drag_flag(self):
        m = self.new_model('patch0.diff')
        self.assertFalse(m.flags(m.indexFromPath('foo')) & Qt.ItemIsDragEnabled)

    def test_status(self):
        m = self.new_model('patch0.diff')
        self.assertEqual('A', m.fileStatus(m.indexFromPath('foo')))
        m = self.new_model('patch1.diff')
        m.setStatusFilter('MARC')
        self.assertEqual('M', m.fileStatus(m.indexFromPath('foo')))
        self.assertEqual('R', m.fileStatus(m.indexFromPath('bar/baz')))

    def test_name_filter(self):
        m = self.new_model('patch0.diff')
        m.setNameFilter('bar')
        self.assertEqual(['bar'], alldata(m))


class ManifestModelReloadTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hg = hg = helpers.HgClient(os.path.join(_tmpdir, cls.__name__))
        hg.init()
        hg.ftouch('foo')
        hg.addremove()
        hg.qnew('patch0.diff')

        hg.qinit('-c')
        hg.commit('--mq', '-m', 'initial state')

        cls.mtimedelay = helpers.guessmtimedelay(hg.path)
        hg.fappend('.hg/hgrc', '[debug]\ndelaylock = %d\n' % cls.mtimedelay)

    def setUp(self):
        repo = thgrepo.repository(path=self.hg.path)
        repo.thginvalidate()  # because of global cache of thgrepo instance
        self.repoagent = thgrepo.RepoAgent(repo)

    def tearDown(self):
        self.hg.revert('-a', '--config', 'debug.delaylock=0')
        self.hg.qpop('-a', '--config', 'debug.delaylock=0')
        self.hg.update('--mq', '-C', '--config', 'debug.delaylock=0')
        self.hg.qpush('-a', '--config', 'debug.delaylock=0')

    def new_model(self, rev=0):
        m = ManifestModel(self.repoagent, rev=rev)
        m.fetchMore(QModelIndex())
        return m

    def add_file(self, name):
        self.hg.ftouch(name)
        self.hg.addremove()
        self.hg.qrefresh()
        self.repoagent.pollStatus()

    def test_samerev_but_node_differs(self):
        m = self.new_model()
        self.assertEqual(['foo'], alldata(m))
        self.add_file('bar')
        m.setRev(m.rev())
        self.assertEqual(['bar', 'foo'], alldata(m))

    def test_samerevctx_but_node_differs(self):
        m = self.new_model()
        self.assertEqual(['foo'], alldata(m))
        self.add_file('bar')
        repo = self.repoagent.rawRepo()
        m.setRawContext(repo[m.rev()])
        self.assertEqual(['bar', 'foo'], alldata(m))

    def add_workingfile(self, name):
        self.hg.ftouch(name)
        self.hg.addremove()
        repo = self.repoagent.rawRepo()
        repo.thginvalidate()

    def test_workingrev_changed(self):
        m = self.new_model(None)
        self.assertEqual(['foo'], alldata(m))
        self.add_workingfile('bar')
        m.setRev(m.rev())
        self.assertEqual(['bar', 'foo'], alldata(m))

    def test_workingctx_changed(self):
        m = self.new_model(None)
        self.assertEqual(['foo'], alldata(m))
        self.add_workingfile('bar')
        repo = self.repoagent.rawRepo()
        m.setRawContext(repo[None])
        self.assertEqual(['bar', 'foo'], alldata(m))

    def test_patchctx_changed(self):
        repo = self.repoagent.rawRepo()
        ctx1 = patchctx.patchctx(repo.mq.join('patch0.diff'), repo)
        ctx1.files()  # load
        self.add_file('bar')
        ctx2 = patchctx.patchctx(repo.mq.join('patch0.diff'), repo)
        ctx2.files()  # load

        m = self.new_model()
        m.setRawContext(ctx1)
        self.assertEqual(['foo'], alldata(m))
        m.setRawContext(ctx2)
        self.assertEqual(['bar', 'foo'], alldata(m))


class ManifestModelLargeFilesTest(unittest.TestCase):
    extensions = ['largefiles']

    @classmethod
    def setUpClass(cls):
        cls.hg = hg = helpers.HgClient(os.path.join(_tmpdir, cls.__name__))
        hg.init()
        hg.fwrite('.hg/hgrc', '[extensions]\nlargefiles=\n')

        hg.ftouch('foo', 'bar', 'large', 'baz/large')
        hg.add('foo', 'bar')
        hg.add('--large', 'large', 'baz/large')
        hg.commit('-m', 'add regular and large files')

        hg.fappend('large', 'hello largefiles\n')
        hg.commit('-m', 'edit large')

    def setUp(self):
        repo = thgrepo.repository(path=self.hg.path)
        self.repoagent = thgrepo.RepoAgent(repo)

    def new_model(self, rev):
        m = ManifestModel(self.repoagent, rev=rev)
        m.fetchMore(QModelIndex())
        return m

    def test_data(self):
        m = self.new_model(0)
        self.assertEqual(['baz', 'bar', 'foo', 'large'], alldata(m))
        self.assertEqual(['large'], alldata(m, m.indexFromPath('baz')))

    def test_status(self):
        m = self.new_model(1)
        self.assertEqual('M', m.fileStatus(m.indexFromPath('large')))
        self.assertEqual('C', m.fileStatus(m.indexFromPath('baz/large')))


_aloha_ja = u'\u3042\u308d\u306f\u30fc'

class ManifestModelEucjpTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # TODO: make this compatible with binary-unsafe filesystem
        if os.name != 'posix' or sys.platform == 'darwin':
            raise SkipTest
        cls.encodingpatch = helpers.patchencoding('euc-jp')

        # include non-ascii char in repo path to test concatenation
        cls.hg = hg = helpers.HgClient(os.path.join(
            _tmpdir, cls.__name__ + _aloha_ja.encode('euc-jp')))
        hg.init()
        hg.ftouch(_aloha_ja.encode('euc-jp'))
        hg.ftouch(_aloha_ja.encode('euc-jp') + '.txt')
        hg.addremove()
        hg.commit('-m', 'add aloha')

    @classmethod
    def tearDownClass(cls):
        cls.encodingpatch.restore()

    def setUp(self):
        repo = thgrepo.repository(path=self.hg.path)
        self.repoagent = thgrepo.RepoAgent(repo)

    def new_model(self):
        m = ManifestModel(self.repoagent, rev=0)
        m.fetchMore(QModelIndex())
        return m

    def test_data(self):
        m = self.new_model()
        self.assertEqual(_aloha_ja, m.data(m.index(0, 0)))

    def test_pathfromindex(self):
        m = self.new_model()
        self.assertEqual(_aloha_ja, m.filePath(m.index(0, 0)))

    def test_indexfrompath(self):
        m = self.new_model()
        self.assertEqual(m.index(0, 0), m.indexFromPath(_aloha_ja))

    def test_fileicon_path_concat(self):
        m = self.new_model()
        m.fileIcon(m.indexFromPath(_aloha_ja + '.txt'))  # no unicode error
