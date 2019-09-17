from __future__ import absolute_import

import time
import unittest

from tortoisehg.hgqt.qtcore import (
    QEventLoop,
    QModelIndex,
    QItemSelectionModel,
    QTimer,
    Qt,
)

from tortoisehg.hgqt import (
    mq,
    thgrepo,
)

import helpers

class PatchQueueModelTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hg = hg = helpers.HgClient(helpers.mktmpdir(cls.__name__))
        hg.init()
        hg.qnew('foo.diff', '-m', 'foo patch')
        hg.qnew('bar.diff')
        hg.qguard('--', '+debug', '-release')
        hg.qnew('baz.diff')
        hg.qpop('-a')
        hg.qinit('-c')
        hg.commit('--mq', '-m', 'initial state')

        cls.mtimedelay = helpers.guessmtimedelay(hg.path)
        hg.fappend('.hg/hgrc', '[debug]\ndelaylock = %d\n' % cls.mtimedelay)

    def setUp(self):
        repo = thgrepo.repository(path=self.hg.path)
        repo.thginvalidate()  # because of global cache of thgrepo instance
        self.repoagent = thgrepo.RepoAgent(repo)
        self.model = mq.PatchQueueModel(self.repoagent)

    def tearDown(self):
        self.hg.qpop('-a', '--config', 'debug.delaylock=0')
        self.hg.update('--mq', '-C', '--config', 'debug.delaylock=0')
        self.repoagent.stopService()
        if self.repoagent.isServiceRunning():
            loop = QEventLoop()
            self.repoagent.serviceStopped.connect(loop.quit)
            QTimer.singleShot(5000, loop.quit)  # timeout
            loop.exec_()

    def indexForPatch(self, patch):
        m = self.model
        indexes = m.match(m.index(0, 0), Qt.EditRole, patch)
        return indexes[0]

    def wait(self, timeout=5000):
        loop = QEventLoop()
        self.repoagent.busyChanged.connect(loop.quit)
        timer = QTimer(interval=timeout, singleShot=True)
        timer.timeout.connect(loop.quit)
        timer.start()
        while self.repoagent.isBusy() and timer.isActive():
            loop.exec_()
        self.assertFalse(self.repoagent.isBusy(), 'timeout while busy')

    def test_patchname(self):
        m = self.model
        self.assertEqual('baz.diff', m.data(m.index(0, 0)))
        self.assertEqual('foo.diff', m.patchName(m.index(2, 0)))

    def test_applied(self):
        self.hg.qpush()
        self.repoagent.pollStatus()
        m = self.model
        self.assertTrue(m.isApplied(self.indexForPatch('foo.diff')))
        self.assertFalse(m.isApplied(self.indexForPatch('bar.diff')))

    def test_tooltip(self):
        m = self.model
        self.assertEqual('foo.diff: no guards\nfoo patch',
                         m.data(self.indexForPatch('foo.diff'), Qt.ToolTipRole))
        self.assertEqual('bar.diff: +debug, -release\n',
                         m.data(self.indexForPatch('bar.diff'), Qt.ToolTipRole))

    def test_patchguards(self):
        m = self.model
        self.assertEqual([], m.patchGuards(self.indexForPatch('foo.diff')))
        self.assertEqual(['+debug', '-release'],
                         m.patchGuards(self.indexForPatch('bar.diff')))

    def test_selection_kept(self):
        m = self.model
        s = QItemSelectionModel(m)
        s.setCurrentIndex(self.indexForPatch('bar.diff'),
                          QItemSelectionModel.SelectCurrent)
        time.sleep(self.mtimedelay)  # qdelete does not obtain lock
        self.hg.qdelete('baz.diff')  # delete first row
        self.repoagent.pollStatus()
        self.assertEqual(self.indexForPatch('bar.diff'), s.currentIndex())
        self.assertEqual([self.indexForPatch('bar.diff')], s.selectedRows())

    def test_selection_deleted(self):
        m = self.model
        s = QItemSelectionModel(m)
        s.setCurrentIndex(self.indexForPatch('bar.diff'),
                          QItemSelectionModel.SelectCurrent)
        time.sleep(self.mtimedelay)  # qdelete does not obtain lock
        self.hg.qdelete('bar.diff')
        self.repoagent.pollStatus()
        self.assertEqual(QModelIndex(), s.currentIndex())
        self.assertEqual([], s.selectedRows())

    def test_selection_renamed(self):
        m = self.model
        s = QItemSelectionModel(m)
        s.setCurrentIndex(self.indexForPatch('bar.diff'),
                          QItemSelectionModel.SelectCurrent)
        time.sleep(self.mtimedelay)  # qrename does not obtain lock
        self.hg.qrename('bar.diff', 'bar2.diff')
        self.repoagent.pollStatus()
        self.assertEqual(self.indexForPatch('bar2.diff'), s.currentIndex())
        self.assertEqual([self.indexForPatch('bar2.diff')], s.selectedRows())

    def test_selection_deleted_renamed(self):
        m = self.model
        s = QItemSelectionModel(m)
        s.setCurrentIndex(self.indexForPatch('baz.diff'),
                          QItemSelectionModel.SelectCurrent)
        time.sleep(self.mtimedelay)  # qdelete/qrename does not obtain lock
        self.hg.qdelete('bar.diff')
        self.hg.qrename('baz.diff', 'baz1.diff')
        self.repoagent.pollStatus()
        self.assertEqual(QModelIndex(), s.currentIndex())
        self.assertEqual([], s.selectedRows())

    def test_dnd_into_top(self):
        m = self.model
        data = m.mimeData([self.indexForPatch('foo.diff')])
        r = m.dropMimeData(data, Qt.MoveAction, 0, 0, QModelIndex())
        self.assertTrue(r)
        self.wait()
        self.assertEqual('foo.diff', m.patchName(m.index(0, 0)))

    def test_dnd_into_bottom(self):
        m = self.model
        data = m.mimeData([self.indexForPatch('baz.diff')])
        r = m.dropMimeData(data, Qt.MoveAction, m.rowCount(), 0, QModelIndex())
        self.assertTrue(r)
        self.wait()
        self.assertEqual('baz.diff', m.patchName(m.index(m.rowCount() - 1, 0)))

    def test_dnd_into_bottom_applied(self):
        self.hg.qpush()
        self.repoagent.pollStatus()
        m = self.model
        data = m.mimeData([self.indexForPatch('baz.diff')])
        r = m.dropMimeData(data, Qt.MoveAction, m.rowCount(), 0, QModelIndex())
        self.assertFalse(r)
