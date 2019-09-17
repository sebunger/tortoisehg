from __future__ import absolute_import

import mock
import os
import unittest

from mercurial import (
    pycompat,
)

from tortoisehg.hgqt.qtcore import (
    QEventLoop,
    QTimer,
)

from tortoisehg.hgqt import thgrepo
from tortoisehg.util import hglib

import helpers

class RepoAgentAttributeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmpdir = helpers.mktmpdir(cls.__name__)
        cls.hg = hg = helpers.HgClient(tmpdir)
        hg.init()
        hg.fappend('foo', '0\n')
        hg.commit('-Am', 'append 0')

        hg.clone('.', '2')
        cls.hg2 = hg2 = helpers.HgClient(os.path.join(tmpdir, '2'))
        hg2.fappend('foo', '1\n')
        hg2.commit('-m', 'append 1')

    def setUp(self):
        ui = hglib.loadui()
        ui.setconfig('tortoisehg', 'monitorrepo', 'never')
        repo = thgrepo.repository(ui, self.hg.path)
        self.agent = thgrepo.RepoAgent(repo)

    def tearDown(self):
        thgrepo._repocache.clear()

    def test_keep_hiddenfilter_on_overlay_change(self):
        self.agent.setHiddenRevsIncluded(True)
        self.agent.setOverlay('union:%s' % self.hg2.path)
        self.assertTrue(self.agent.hiddenRevsIncluded())
        self.agent.setHiddenRevsIncluded(False)
        self.agent.clearOverlay()
        self.assertFalse(self.agent.hiddenRevsIncluded())


class _RepoAgentChangedSignalTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmpdir = helpers.mktmpdir(cls.__name__)
        cls.srchg = hg = helpers.HgClient(tmpdir)
        hg.init()
        for i in pycompat.xrange(2):
            hg.fappend('foo', '%d\n' % i)
            hg.commit('-Am', 'append %d' % i)

        hg.clone('.', '2')
        cls.hg2 = hg2 = helpers.HgClient(os.path.join(tmpdir, '2'))
        hg2.fappend('foo', '2\n')
        hg2.commit('-m', 'append 2')

        cls.mtimedelay = helpers.guessmtimedelay(tmpdir)

    def setUp(self):
        testname = self.id().split('.')[-1]
        self.srchg.clone('--pull', '.', testname)  # --pull for rollback
        self.hg = helpers.HgClient(os.path.join(self.srchg.path, testname))
        self.hg.fappend('.hg/hgrc',
                        '[debug]\ndelaylock = %d\n' % self.mtimedelay)
        ui = hglib.loadui()
        ui.setconfig('tortoisehg', 'monitorrepo', self.monitorrepo)
        repo = thgrepo.repository(ui, self.hg.path)
        self.agent = agent = thgrepo.RepoAgent(repo)
        self.repositoryChanged = mock.Mock()
        agent.repositoryChanged.connect(self.repositoryChanged)
        agent.startMonitoringIfEnabled()

    def tearDown(self):
        self.agent.stopService()
        if self.agent.isServiceRunning():
            loop = QEventLoop()
            self.agent.serviceStopped.connect(loop.quit)
            QTimer.singleShot(5000, loop.quit)  # timeout
            loop.exec_()
        thgrepo._repocache.clear()

    def wait(self, timeout=5000):
        loop = QEventLoop()
        self.agent.busyChanged.connect(loop.quit)
        timer = QTimer(interval=timeout, singleShot=True)
        timer.timeout.connect(loop.quit)
        timer.start()
        while self.agent.isBusy() and timer.isActive():
            loop.exec_()
        self.assertFalse(self.agent.isBusy(), 'timeout while busy')

    def wait_changed(self, flags, timeout=5000):
        self.repositoryChanged.reset_mock()
        loop = QEventLoop()
        self.agent.repositoryChanged.connect(loop.quit)
        QTimer.singleShot(timeout, loop.quit)
        loop.exec_()
        self.repositoryChanged.assert_called_once_with(flags)
        self.assertFalse(self.agent.isBusy(),
                         'repositoryChanged emitted while busy')

    def test_no_changed_signal_while_command_running(self):
        self.agent.runCommand(['update', '0',
                               '--config', 'debug.delaylock=2000'])
        self.hg.update('0')
        self.wait_changed(thgrepo.WorkingParentChanged
                          | thgrepo.WorkingStateChanged)

    def test_poll_on_command_finished(self):
        self.agent.runCommandSequence([['update', '0'], ['root']])
        self.wait_changed(thgrepo.WorkingParentChanged
                          | thgrepo.WorkingStateChanged)

    def test_rollback_to_null(self):
        self.agent.runCommand(['rollback'])
        # it seems "rollback" does not touch dirstate
        self.wait_changed(thgrepo.LogChanged
                          | thgrepo.WorkingParentChanged
                          | thgrepo.WorkingStateChanged)

    def test_rollback_commit(self):
        self.hg.ftouch('bar')
        self.agent.runCommand(['commit', '-Am', 'change'])
        self.wait_changed(thgrepo.LogChanged
                          | thgrepo.WorkingParentChanged
                          | thgrepo.WorkingStateChanged)
        self.agent.runCommand(['rollback'])  # mtime of dirstate will go back
        self.wait_changed(thgrepo.LogChanged
                          | thgrepo.WorkingParentChanged
                          | thgrepo.WorkingStateChanged)

    def test_branch_changed(self):
        self.agent.runCommand(['branch', 'foo'])
        self.wait_changed(thgrepo.WorkingBranchChanged)

    def test_branch_and_parent_changed(self):
        self.agent.runCommandSequence([['update', '0'],
                                       ['branch', 'foo']])
        self.wait_changed(thgrepo.WorkingBranchChanged
                          | thgrepo.WorkingParentChanged
                          | thgrepo.WorkingStateChanged)

    def test_listen_to_new_queue_changes(self):
        self.agent.runCommand(['qqueue', '-c', 'foo'])
        self.wait_changed(thgrepo.LogChanged)
        self.agent.runCommandSequence([['export', 'tip', '-o', 'patch'],
                                       ['qimport', 'patch']])
        self.wait_changed(thgrepo.LogChanged)

    def test_invalidate_on_dirstate_changed(self):
        repo = self.agent.rawRepo()
        self.assertEqual({'foo'}, set(repo.dirstate))  # preload cache
        self.hg.ftouch('bar')
        self.agent.runCommand(['add', 'bar'])
        self.wait()
        self.assertEqual({'bar', 'foo'}, set(repo.dirstate))

    def test_immediate_hiddenfilter(self):
        self.agent.setHiddenRevsIncluded(not self.agent.hiddenRevsIncluded())
        self.repositoryChanged.assert_called_once_with(thgrepo.LogChanged)

    def test_hiddenfilter_while_command_running(self):
        self.agent.runCommand(['root'])
        self.agent.setHiddenRevsIncluded(not self.agent.hiddenRevsIncluded())
        self.assertFalse(self.repositoryChanged.called)
        self.wait_changed(thgrepo.LogChanged)

    def test_immediate_overlay(self):
        self.agent.setOverlay('union:%s' % self.hg2.path)
        self.repositoryChanged.assert_called_once_with(thgrepo.LogChanged)
        self.repositoryChanged.reset_mock()
        self.agent.clearOverlay()
        self.repositoryChanged.assert_called_once_with(thgrepo.LogChanged)

    def test_overlay_while_command_running(self):
        self.agent.runCommand(['root'])
        self.agent.setOverlay('union:%s' % self.hg2.path)
        self.assertFalse(self.repositoryChanged.called)
        self.wait_changed(thgrepo.LogChanged)

    def test_clearoverlay_while_command_running(self):
        self.agent.setOverlay('union:%s' % self.hg2.path)
        self.repositoryChanged.reset_mock()
        self.agent.runCommand(['root'])
        self.agent.clearOverlay()
        self.assertFalse(self.repositoryChanged.called)
        self.wait_changed(thgrepo.LogChanged)


class RepoAgentChangedSignalWithMonitorTest(_RepoAgentChangedSignalTestBase):
    monitorrepo = 'always'

    def test_filesystem_watcher(self):
        self.hg.update('0')
        self.wait_changed(thgrepo.WorkingParentChanged
                          | thgrepo.WorkingStateChanged)

    def test_resume_monitoring_while_command_running(self):
        self.agent.suspendMonitoring()
        self.agent.runCommand(['root'])
        self.agent.resumeMonitoring()
        self.wait()
        self.hg.update('0')
        self.wait_changed(thgrepo.WorkingParentChanged
                          | thgrepo.WorkingStateChanged)

    def test_resume_monitoring_with_overlay(self):
        self.agent.suspendMonitoring()
        self.agent.setOverlay('union:%s' % self.hg2.path)
        self.agent.resumeMonitoring()
        self.agent.clearOverlay()
        self.hg.update('0')
        self.wait_changed(thgrepo.WorkingParentChanged
                          | thgrepo.WorkingStateChanged)


class RepoAgentChangedSignalWithoutMonitorTest(_RepoAgentChangedSignalTestBase):
    monitorrepo = 'never'
