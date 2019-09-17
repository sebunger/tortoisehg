from __future__ import absolute_import

import mock
import os
import unittest

from tortoisehg.hgqt.qtcore import (
    QEventLoop,
    QTimer,
)

from tortoisehg.hgqt import (
    cmdcore,
    thgrepo,
)
from tortoisehg.util import hglib

import helpers

def mockrepo(ui, path):
    m = mock.MagicMock(ui=ui, root=path)
    m.unfiltered = lambda: m
    m.filtered = lambda name: m
    return m

def mockwatcher(repo, parent=None):
    m = mock.MagicMock()
    m.isMonitoring.return_value = False
    return m

if os.name == 'nt':
    def fspath(s):
        if s.startswith('/'):
            s = 'C:' + s
        return s.replace('/', os.sep)
else:
    def fspath(s):
        return s

LOCAL_SIGNALS = ['repositoryOpened', 'repositoryClosed']
MAPPED_SIGNALS = [
    # signal name, example arguments
    ('configChanged', ()),
    ('repositoryChanged', (thgrepo.LogChanged,)),
    ('repositoryDestroyed', ()),
    ('busyChanged', (False,)),
    ('progressReceived', (cmdcore.ProgressMessage('', None),)),
    ]

class RepoManagerMockedTest(unittest.TestCase):
    def setUp(self):
        self.hgrepopatcher = mock.patch('mercurial.hg.repository', new=mockrepo)
        self.watcherpatcher = mock.patch('tortoisehg.hgqt.thgrepo.RepoWatcher',
                                         new=mockwatcher)
        self.hgrepopatcher.start()
        self.watcherpatcher.start()
        self.repoman = thgrepo.RepoManager(hglib.loadui())

        for signame in LOCAL_SIGNALS + [s for s, _a in MAPPED_SIGNALS]:
            slot = mock.Mock()
            setattr(self, signame, slot)
            getattr(self.repoman, signame).connect(slot)

    def tearDown(self):
        self.watcherpatcher.stop()
        self.hgrepopatcher.stop()
        thgrepo._repocache.clear()

    def test_cached(self):
        a1 = self.repoman.openRepoAgent('/a')
        a2 = self.repoman.openRepoAgent('/a')
        self.assertTrue(a1 is a2)

    def test_release(self):
        self.repoman.openRepoAgent('/a')
        self.repoman.openRepoAgent('/a')

        self.repoman.releaseRepoAgent('/a')
        self.assertTrue(self.repoman.repoAgent('/a'))

        self.repoman.releaseRepoAgent('/a')
        self.assertFalse(self.repoman.repoAgent('/a'))

    def test_sub_release(self):
        a = self.repoman.openRepoAgent('/a')
        b1 = a.subRepoAgent('b')
        b2 = a.subRepoAgent('b')
        self.assertTrue(b1 is b2)
        self.assertTrue(self.repoman.repoAgent('/a/b'))

        self.repoman.releaseRepoAgent('/a')
        self.assertFalse(self.repoman.repoAgent('/a/b'))

    def test_sub_already_open(self):
        a = self.repoman.openRepoAgent('/a')
        b1 = self.repoman.openRepoAgent('/a/b')
        b2 = a.subRepoAgent('b')
        self.assertTrue(b1 is b2)

        self.repoman.releaseRepoAgent('/a')
        self.assertTrue(self.repoman.repoAgent('/a/b'))
        self.repoman.releaseRepoAgent('/a/b')
        self.assertFalse(self.repoman.repoAgent('/a/b'))

    def test_sub_invalidpath(self):
        a = self.repoman.openRepoAgent('/a')
        a.subRepoAgent('/a/b')  # ok
        a.subRepoAgent('../a/b')  # ok
        self.assertRaises(ValueError, lambda: a.subRepoAgent('/a'))
        self.assertRaises(ValueError, lambda: a.subRepoAgent('/b'))
        self.assertRaises(ValueError, lambda: a.subRepoAgent('../a'))

    def test_sub_rootedpath(self):
        a = self.repoman.openRepoAgent('/')
        a.subRepoAgent('/a')  # ok
        self.assertRaises(ValueError, lambda: a.subRepoAgent('/'))

    def test_signal_map(self):
        p = fspath('/a')
        a = self.repoman.openRepoAgent(p)
        for signame, args in MAPPED_SIGNALS:
            getattr(a, signame).emit(*args)
            fullargs = (p,) + args
            getattr(self, signame).assert_called_once_with(*fullargs)

    def test_disconnect_signal_on_close(self):
        a = self.repoman.openRepoAgent('/a')
        self.repoman.releaseRepoAgent('/a')
        for signame, args in MAPPED_SIGNALS:
            getattr(a, signame).emit(*args)
            self.assertFalse(getattr(self, signame).called)

    def test_opened_signal(self):
        p = fspath('/a')
        self.repoman.repositoryOpened.connect(
            lambda: self.assertTrue(self.repoman.repoAgent(p)))
        self.repoman.openRepoAgent(p)
        self.repositoryOpened.assert_called_once_with(p)
        self.repositoryOpened.reset_mock()
        # emitted only if repository is actually instantiated (i.e. not cached)
        self.repoman.openRepoAgent(p)
        self.assertFalse(self.repositoryOpened.called)

    def test_closed_signal(self):
        p = fspath('/a')
        self.repoman.repositoryClosed.connect(
            lambda: self.assertFalse(self.repoman.repoAgent(p)))
        self.repoman.openRepoAgent(p)
        self.repoman.openRepoAgent(p)
        self.repoman.releaseRepoAgent(p)
        self.assertFalse(self.repositoryClosed.called)
        self.repoman.releaseRepoAgent(p)
        self.repositoryClosed.assert_called_once_with(p)


def waitForRepositoryClosed(repoman, path, timeout=5000):
    loop = QEventLoop()
    repoman.repositoryClosed.connect(loop.quit)
    timer = QTimer(interval=timeout, singleShot=True)
    timer.timeout.connect(loop.quit)
    timer.start()
    while repoman.repoAgent(path) and timer.isActive():
        loop.exec_()

def waitForServiceStopped(repoagent, timeout=5000):
    if not repoagent.isServiceRunning():
        return
    loop = QEventLoop()
    repoagent.serviceStopped.connect(loop.quit)
    QTimer.singleShot(timeout, loop.quit)
    loop.exec_()

def waitForUnbusy(repoagent, timeout=5000):
    if not repoagent.isBusy():
        return
    loop = QEventLoop()
    repoagent.busyChanged.connect(loop.quit)
    QTimer.singleShot(timeout, loop.quit)
    loop.exec_()


class RepoManagerServiceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmpdir = helpers.mktmpdir(cls.__name__)
        cls.hg = hg = helpers.HgClient(tmpdir)
        hg.init()

    def setUp(self):
        ui = hglib.loadui()
        ui.setconfig('tortoisehg', 'cmdworker', 'server')
        ui.setconfig('tortoisehg', 'monitorrepo', 'never')
        self.repoman = thgrepo.RepoManager(ui)

    def tearDown(self):
        if self.repoman.repoAgent(self.hg.path):
            self.repoman.releaseRepoAgent(self.hg.path)
            waitForRepositoryClosed(self.repoman, self.hg.path)
        thgrepo._repocache.clear()

    def test_close(self):
        a = self.repoman.openRepoAgent(self.hg.path)
        a.runCommand(['root'])  # start service
        waitForUnbusy(a)
        self.assertTrue(a.isServiceRunning())
        self.repoman.releaseRepoAgent(self.hg.path)
        self.assertTrue(self.repoman.repoAgent(self.hg.path))
        waitForRepositoryClosed(self.repoman, self.hg.path)
        self.assertFalse(self.repoman.repoAgent(self.hg.path))

    def test_reopen_about_to_be_closed(self):
        a1 = self.repoman.openRepoAgent(self.hg.path)
        a1.runCommand(['root'])  # start service
        waitForUnbusy(a1)
        self.repoman.releaseRepoAgent(self.hg.path)
        # increase refcount again
        a2 = self.repoman.openRepoAgent(self.hg.path)
        self.assertTrue(a1 is a2)
        # repository should be available after service stopped
        waitForServiceStopped(a1)
        self.assertTrue(self.repoman.repoAgent(self.hg.path))
