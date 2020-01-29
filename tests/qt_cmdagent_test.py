from __future__ import absolute_import

import mock
import unittest

from mercurial import (
    pycompat,
)

from tortoisehg.hgqt.qtcore import (
    QBuffer,
    QCoreApplication,
    QEventLoop,
    QIODevice,
    QObject,
    QTimer,
    pyqtSlot,
)

from tortoisehg.hgqt import cmdcore
from tortoisehg.util import hglib

import helpers

class CmdWaiter(QObject):
    def __init__(self, session):
        super(CmdWaiter, self).__init__()
        self._session = session
        self._outputs = []
        self._session.outputReceived.connect(self._captureOutput)

    def outputString(self):
        return ''.join(self._outputs).rstrip()

    def wait(self, timeout=5000):
        if self._session.isFinished():
            return
        loop = QEventLoop()
        self._session.commandFinished.connect(loop.quit)
        QTimer.singleShot(timeout, loop.quit)
        loop.exec_()

    @pyqtSlot(str, str)
    def _captureOutput(self, msg, label):
        if not label:
            self._outputs.append(pycompat.unicode(msg))


def waitForCmdStarted(session, timeout=5000):
    if session.isRunning() or session.isFinished():
        return
    loop = QEventLoop()
    session.controlMessage.connect(loop.quit)  # wait for initial banner
    QTimer.singleShot(timeout, loop.quit)
    loop.exec_()


class _CmdAgentTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tmpdir = helpers.mktmpdir(cls.__name__)
        cls.hg = hg = helpers.HgClient(tmpdir)
        hg.init()
        hg.ftouch('foo')
        hg.commit('-Am', 'add foo')

    def setUp(self):
        ui = hglib.loadui()
        self.agent = agent = cmdcore.CmdAgent(ui, cwd=self.hg.path,
                                              worker=self.workername)
        self.busyChanged = mock.Mock()
        self.commandFinished = mock.Mock()
        agent.busyChanged.connect(self.busyChanged)
        agent.commandFinished.connect(self.commandFinished)

    def tearDown(self):
        self.agent.stopService()
        if self.agent.isServiceRunning():
            loop = QEventLoop()
            self.agent.serviceStopped.connect(loop.quit)
            QTimer.singleShot(5000, loop.quit)  # timeout
            loop.exec_()

    def test_runcommand(self):
        sess = self.agent.runCommand(['root'])
        self._check_runcommand(sess, self.hg.path)

    def test_runcommandseq(self):
        sess = self.agent.runCommandSequence([['root'], ['id', '-i']])
        self._check_runcommand(sess, '\n'.join([self.hg.path, '53245c60e682']))

    def test_runcommandseq_firsterror(self):
        sess = self.agent.runCommandSequence([['id', '-r100'], ['root']])
        self._check_runcommand(sess, '', 255)

    def test_runcommand_delayedstart(self):
        sess = self.agent.runCommand(['root'])
        self.assertFalse(sess.isRunning())
        waitForCmdStarted(sess)
        self.assertTrue(sess.isRunning())
        self._check_runcommand(sess, self.hg.path)

    def test_runcommand_queued(self):
        sess1 = self.agent.runCommand(['id', '-i'])
        waitForCmdStarted(sess1)
        self.assertTrue(sess1.isRunning())
        sess2 = self.agent.runCommand(['id', '-n'])
        self.assertFalse(sess2.isRunning())

        self._check_runcommand(sess1, '53245c60e682')
        QCoreApplication.processEvents()  # should start in next loop
        self.assertTrue(sess2.isRunning())
        self._check_runcommand(sess2, '0')

    def test_runcommand_signal_chain(self):
        sess = self.agent.runCommand(['id', '-i'])
        chainedsessq = []
        sess.commandFinished.connect(
            lambda: chainedsessq.append(self.agent.runCommand(['id', '-n'])))
        self._check_runcommand(sess, '53245c60e682')
        self.assertTrue(chainedsessq)
        sess = chainedsessq.pop(0)
        QCoreApplication.processEvents()  # should start in next loop
        self.assertTrue(sess.isRunning())
        self._check_runcommand(sess, '0')

    def test_captureout(self):
        sess = self.agent.runCommandSequence(
            [['root'], ['id', '-i'], ['cat', 'unknown']])
        sess.setCaptureOutput(True)
        readyRead = mock.Mock()
        sess.readyRead.connect(readyRead)
        self._check_runcommand(sess, '', 1)
        self.assertTrue('no such file' in sess.warningString())  # not captured
        self.assertTrue(readyRead.called)
        self.assertTrue(sess.canReadLine())
        self.assertEqual(self.hg.path + '\n', sess.readLine())
        self.assertEqual('5', sess.read(1))
        self.assertEqual('3', str(sess.peek(1)))
        self.assertEqual(b'3245c60e682\n', bytes(sess.readAll()))

    def _check_runcommand(self, sess, expectedout, expectedcode=0):
        self.assertFalse(sess.isFinished())
        waiter = CmdWaiter(sess)
        waiter.wait()
        self.assertTrue(sess.isFinished())
        self.assertFalse(sess.isRunning())
        self.assertEqual(expectedcode, sess.exitCode())
        self.assertEqual(expectedout, waiter.outputString())
        self.commandFinished.assert_any_call(sess)

    def test_abort_session(self):
        sess = self.agent.runCommand(['log'])
        finished = mock.Mock()
        sess.commandFinished.connect(finished)
        waitForCmdStarted(sess)
        self.assertTrue(sess.isRunning())
        sess.abort()
        self._check_abort_session(sess)
        self.assertEqual(1, finished.call_count)

    def test_abort_session_not_running(self):
        sess1 = self.agent.runCommand(['id', '-i'])
        sess2 = self.agent.runCommand(['id', '-n'])
        finished = mock.Mock()
        sess1.commandFinished.connect(finished.sess1)
        sess2.commandFinished.connect(finished.sess2)

        # waiting session aborts immediately
        sess2.abort()
        self.assertTrue(sess2.isAborted())
        self.assertTrue(sess2.isFinished())
        CmdWaiter(sess1).wait()
        # "finished" signal of waiting session should be emitted, because the
        # session object is known to the client
        self.assertEqual(['sess2', 'sess1'],
                         [x[0] for x in finished.method_calls])
        # but agent's signal should be emitted only for the active session
        self.assertEqual([mock.call(sess1)],
                         self.commandFinished.call_args_list)

    def test_abort_all_waiting_sessions(self):
        sessions = pycompat.maplist(self.agent.runCommand,
                                    [['id', '-i'], ['id', '-n'], ['root']])
        self.assertTrue(self.agent.isBusy())
        self.busyChanged.reset_mock()
        # abort from waiting one
        for sess in sessions[1:] + [sessions[0]]:
            sess.abort()
            self.assertTrue(sess.isAborted())
            self.assertTrue(sess.isFinished())
        # sessions should be deleted from queue immediately
        self.assertFalse(self.agent.isBusy())
        self.busyChanged.assert_called_once_with(False)

    def test_abortcommands(self):
        sessions = pycompat.maplist(self.agent.runCommand,
                                    [['id', '-i'], ['id', '-n'], ['root']])
        waitForCmdStarted(sessions[0])
        # sess0 (running), sess1 (waiting), ...
        self.agent.abortCommands()
        for sess in sessions:
            self._check_abort_session(sess)
        self.assertFalse(self.agent.isBusy())

    def _check_abort_session(self, sess):
        waiter = CmdWaiter(sess)
        waiter.wait()
        self.assertTrue(sess.isAborted())
        self.assertTrue(sess.isFinished())
        self.assertFalse(sess.isRunning())

    def test_busystate(self):
        self.assertFalse(self.agent.isBusy())
        sess = self.agent.runCommand(['id'])
        self.assertTrue(self.agent.isBusy())
        self.busyChanged.assert_called_once_with(True)
        self.busyChanged.reset_mock()

        CmdWaiter(sess).wait()
        self.assertFalse(self.agent.isBusy())
        self.busyChanged.assert_called_once_with(False)

    def test_busystate_queued(self):
        sess1 = self.agent.runCommand(['id'])
        self.busyChanged.assert_called_once_with(True)
        self.busyChanged.reset_mock()

        sess2 = self.agent.runCommand(['id'])
        self.assertTrue(self.agent.isBusy())

        CmdWaiter(sess1).wait()
        self.assertTrue(self.agent.isBusy())
        self.assertFalse(self.busyChanged.called)

        CmdWaiter(sess2).wait()
        self.assertFalse(self.agent.isBusy())
        self.busyChanged.assert_called_once_with(False)

    def test_busystate_on_finished(self):
        self.agent.commandFinished.connect(self._check_busystate_on_finished)
        sess = self.agent.runCommand(['id'])
        CmdWaiter(sess).wait()

    def _check_busystate_on_finished(self):
        # busy state should be off when the last commandFinished emitted
        self.assertFalse(self.agent.isBusy())


class CmdAgentProcTest(_CmdAgentTestBase):
    workername = 'proc'


class CmdAgentServerTest(_CmdAgentTestBase):
    workername = 'server'

    @classmethod
    def setUpClass(cls):
        super(CmdAgentServerTest, cls).setUpClass()
        cls.hg.fwrite('testext.py',
                      'from binascii import unhexlify\n'
                      'from mercurial import registrar\n'
                      'cmdtable = {}\n'
                      'command = registrar.command(cmdtable)\n'
                      '@command(b"echoback")\n'
                      'def echoback(ui, repo):\n'
                      '    ui.write(ui.fin.read())\n'
                      '@command(b"writestdout")\n'
                      'def writestdout(ui, repo, *data):\n'
                      '    stdout = ui.fout.out\n'
                      '    stdout.write("".join(map(unhexlify, data)))\n'
                      '    stdout.flush()\n')
        cls.hg.fappend('.hg/hgrc', '[extensions]\ntestext = testext.py\n')

    def test_abort_session_waiting_for_worker(self):
        sess = self.agent.runCommand(['id', '-i'])
        QCoreApplication.processEvents()  # start session
        self.assertTrue(sess._worker)
        self.assertNotEqual(cmdcore.CmdWorker.Ready,
                            sess._worker.serviceState())
        sess.abort()
        CmdWaiter(sess).wait()
        self.assertTrue(sess.isAborted())

    def test_runcommand_while_service_stopping(self):
        sess1 = self.agent.runCommand(['id', '-i'])  # start server
        CmdWaiter(sess1).wait()
        worker = self.agent._worker
        self.assertEqual(cmdcore.CmdWorker.Ready, worker.serviceState())
        self.agent.stopService()
        self.assertEqual(cmdcore.CmdWorker.Stopping, worker.serviceState())
        # start new session while server is shutting down
        sess2 = self.agent.runCommand(['id', '-n'])
        CmdWaiter(sess2).wait()
        self.assertTrue(sess2.isFinished())
        self.assertEqual(0, sess2.exitCode())  # should not be canceled

    @mock.patch('tortoisehg.util.paths.get_hg_command',
                return_value=['/inexistent'])
    def test_server_failed_to_start(self, m):
        sess = self.agent.runCommand(['id', '-i'])
        CmdWaiter(sess).wait()
        self.assertTrue(sess.isFinished())
        self.assertEqual(-1, sess.exitCode())

    def test_stop_server_by_data_timeout(self):
        CmdWaiter(self.agent.runCommand(['id'])).wait()  # start server
        worker = self.agent._worker
        worker._readtimer.setInterval(100)  # avoid long wait
        sess = self.agent.runCommand(['writestdout',
                                      'o'.encode('hex'), '00000001'])
        CmdWaiter(sess).wait()
        self.assertEqual(cmdcore.CmdWorker.NotRunning, worker.serviceState())

    def test_stop_server_by_unexpected_required_channel(self):
        CmdWaiter(self.agent.runCommand(['id'])).wait()  # start server
        worker = self.agent._worker
        sess = self.agent.runCommand(['writestdout',
                                      'X'.encode('hex'), '00000000'])
        CmdWaiter(sess).wait()
        failstates = (cmdcore.CmdWorker.Stopping, cmdcore.CmdWorker.NotRunning)
        self.assertTrue(worker.serviceState() in failstates)

    def test_unicode_error_in_runcommand(self):
        sess = self.agent.runCommand(['files', '-X', u'\u3000'])
        CmdWaiter(sess).wait()
        self.assertEqual(-1, sess.exitCode())
        self.assertTrue('failed to encode command' in sess.errorString())

    def test_data_input(self):
        buf = QBuffer()
        buf.setData(b'foo')
        buf.open(QIODevice.ReadOnly)
        sess = self.agent.runCommand(['echoback'])
        sess.setInputDevice(buf)
        self._check_runcommand(sess, b'foo')

    def test_data_input_unset(self):
        sess = self.agent.runCommand(['echoback'])
        self._check_runcommand(sess, b'')
