# cmdcore.py - run Mercurial commands in a separate thread or process
#
# Copyright 2010 Yuki KODAMA <endflow.net@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import os, signal, time

from PyQt4.QtCore import QIODevice, QObject, QProcess, QTimer
from PyQt4.QtCore import pyqtSignal, pyqtSlot

from tortoisehg.util import hglib, paths
from tortoisehg.hgqt.i18n import _
from tortoisehg.hgqt import thread

class CmdProc(QObject):
    'Run mercurial command in separate process'

    started = pyqtSignal()
    commandFinished = pyqtSignal(int)
    outputReceived = pyqtSignal(unicode, unicode)

    # progress is not supported but needed to be a worker class
    progressReceived = pyqtSignal(unicode, object, unicode, unicode, object)

    def __init__(self, cmdline, parent=None):
        super(CmdProc, self).__init__(parent)
        self.cmdline = cmdline

        self._proc = proc = QProcess(self)
        proc.started.connect(self.started)
        proc.finished.connect(self.commandFinished)
        proc.readyReadStandardOutput.connect(self._stdout)
        proc.readyReadStandardError.connect(self._stderr)
        proc.error.connect(self._handleerror)

    def start(self):
        fullcmdline = paths.get_hg_command() + self.cmdline
        self._proc.start(fullcmdline[0], fullcmdline[1:], QIODevice.ReadOnly)

    def abort(self):
        if not self.isRunning():
            return
        if os.name == 'nt':
            # TODO: do not TerminateProcess(); send CTRL_C_EVENT in some way
            self._proc.close()
        else:
            os.kill(int(self._proc.pid()), signal.SIGINT)

    def isRunning(self):
        return self._proc.state() != QProcess.NotRunning

    def _handleerror(self, error):
        if error == QProcess.FailedToStart:
            self.outputReceived.emit(_('failed to start command\n'),
                                     'ui.error')
            self.commandFinished.emit(-1)
        elif error != QProcess.Crashed:
            self.outputReceived.emit(_('error while running command\n'),
                                     'ui.error')

    def _stdout(self):
        data = self._proc.readAllStandardOutput().data()
        self.outputReceived.emit(hglib.tounicode(data), '')

    def _stderr(self):
        data = self._proc.readAllStandardError().data()
        self.outputReceived.emit(hglib.tounicode(data), 'ui.error')


def _quotecmdarg(arg):
    # only for display; no use to construct command string for os.system()
    if not arg or ' ' in arg or '\\' in arg or '"' in arg:
        return '"%s"' % arg.replace('"', '\\"')
    else:
        return arg

def _prettifycmdline(cmdline):
    r"""Build pretty command-line string for display

    >>> _prettifycmdline(['--repository', 'foo', 'status'])
    'status'
    >>> _prettifycmdline(['--cwd', 'foo', 'resolve', '--', '--repository'])
    'resolve -- --repository'
    >>> _prettifycmdline(['log', 'foo\\bar', '', 'foo bar', 'foo"bar'])
    'log "foo\\bar" "" "foo bar" "foo\\"bar"'
    """
    try:
        argcount = cmdline.index('--')
    except ValueError:
        argcount = len(cmdline)
    printables = []
    pos = 0
    while pos < argcount:
        if cmdline[pos] in ('-R', '--repository', '--cwd'):
            pos += 2
        else:
            printables.append(cmdline[pos])
            pos += 1
    printables.extend(cmdline[argcount:])

    return ' '.join(_quotecmdarg(e) for e in printables)

class CmdSession(QObject):
    """Run Mercurial commands in a background thread or process"""

    commandFinished = pyqtSignal(int)

    outputReceived = pyqtSignal(unicode, unicode)
    progressReceived = pyqtSignal(unicode, object, unicode, unicode, object)

    # TODO: instead of useproc, run() will receive worker instance
    def __init__(self, cmdlines, parent=None, display=None, useproc=False):
        super(CmdSession, self).__init__(parent)

        self._worker = None
        self._queue = list(cmdlines)
        self._display = display
        self._useproc = useproc
        self._abortbyuser = False
        self._erroroutputs = []
        self._warningoutputs = []
        self._exitcode = 0

    ### Public Methods ###

    def run(self):
        '''Execute Mercurial command'''
        if self.isRunning() or not self._queue:
            return
        if self._abortbyuser:
            # -1 instead of 255 for compatibility with CmdThread
            self._finish(-1)
            return
        self._runNext()

    def abort(self):
        '''Cancel running Mercurial command'''
        if self.isRunning():
            self._worker.abort()
            del self._queue[:]
            self._abortbyuser = True
        elif not self.isFinished():
            # don't abort immediately because this hasn't started yet
            self._abortbyuser = True

    def isAborted(self):
        """True if commands have finished by user abort"""
        return self.isFinished() and self._abortbyuser

    def isFinished(self):
        """True if all pending commands have finished or been aborted"""
        return not self._queue and not self.isRunning()

    def isRunning(self):
        """True if a command is running; False if finished or not started yet"""
        # keep "running" until just before emitting commandFinished. if worker
        # is QThread, isRunning() is cleared earlier than _onCommandFinished,
        # because inter-thread signal is queued.
        return bool(self._worker)

    def errorString(self):
        """Error message received in the last command"""
        if self._abortbyuser:
            return _('Terminated by user')
        else:
            return ''.join(self._erroroutputs).rstrip()

    def warningString(self):
        """Warning message received in the last command"""
        return ''.join(self._warningoutputs).rstrip()

    def exitCode(self):
        """Integer return code of the last command"""
        return self._exitcode

    ### Private Method ###

    def _createWorker(self, cmdline):
        cmdline = map(hglib.fromunicode, cmdline)
        if self._useproc:
            return CmdProc(cmdline, self)
        else:
            return thread.CmdThread(cmdline, self)

    def _runNext(self):
        cmdline = self._queue.pop(0)

        if not self._display:
            self._display = _prettifycmdline(cmdline)
        self._worker = self._createWorker(cmdline)
        self._worker.started.connect(self._onCommandStarted)
        self._worker.commandFinished.connect(self._onCommandFinished)

        self._worker.outputReceived.connect(self.outputReceived)
        self._worker.outputReceived.connect(self._captureOutput)
        self._worker.progressReceived.connect(self.progressReceived)

        self._abortbyuser = False
        del self._erroroutputs[:]
        del self._warningoutputs[:]
        self._worker.start()

    def _finish(self, ret):
        del self._queue[:]
        self._worker = None
        self._exitcode = ret
        self.commandFinished.emit(ret)

    ### Signal Handlers ###

    @pyqtSlot()
    def _onCommandStarted(self):
        cmd = '%% hg %s\n' % self._display
        self.outputReceived.emit(cmd, 'control')

    @pyqtSlot(int)
    def _onCommandFinished(self, ret):
        if ret == -1:
            if self._abortbyuser:
                msg = _('[command terminated by user %s]')
            else:
                msg = _('[command interrupted %s]')
        elif ret:
            msg = _('[command returned code %d %%s]') % ret
        else:
            msg = _('[command completed successfully %s]')
        self.outputReceived.emit(msg % time.asctime() + '\n', 'control')

        self._display = None
        self._worker.setParent(None)  # assist gc
        if ret != 0 or not self._queue:
            self._finish(ret)
        else:
            self._runNext()

    @pyqtSlot(unicode, unicode)
    def _captureOutput(self, msg, label):
        if not label:
            return  # fast path
        labelset = unicode(label).split()
        # typically ui.error is sent only once at end
        if 'ui.error' in labelset:
            self._erroroutputs.append(unicode(msg))
        elif 'ui.warning' in labelset:
            self._warningoutputs.append(unicode(msg))


def nullCmdSession():
    """Finished CmdSession object which can be used as the initial value

    >>> sess = nullCmdSession()
    >>> sess.isFinished(), sess.isRunning(), sess.isAborted()
    (True, False, False)
    >>> sess.abort()  # should not change flags
    >>> sess.isFinished(), sess.isRunning(), sess.isAborted()
    (True, False, False)
    """
    return CmdSession([])


# TODO: remove with increment/decrementBusyCount
class _RunningCmdSession(CmdSession):
    def abort(self):
        pass
    def isRunning(self):
        return True

def runningCmdSession():
    """CmdSession object which can be used as a stub for busy count

    >>> sess = runningCmdSession()
    >>> sess.isFinished(), sess.isRunning(), sess.isAborted()
    (False, True, False)
    >>> sess.run()  # do nothing
    >>> sess.isFinished(), sess.isRunning(), sess.isAborted()
    (False, True, False)
    >>> sess.abort()  # do nothing
    >>> sess.isFinished(), sess.isRunning(), sess.isAborted()
    (False, True, False)
    """
    return _RunningCmdSession([])


class CmdAgent(QObject):
    """Manage requests of Mercurial commands"""

    busyChanged = pyqtSignal(bool)
    outputReceived = pyqtSignal(unicode, unicode)
    progressReceived = pyqtSignal(unicode, object, unicode, unicode, object)

    def __init__(self, parent=None):
        super(CmdAgent, self).__init__(parent)
        self._cwd = None
        self._sessqueue = []  # [active, waiting...]
        self._runlater = QTimer(self, interval=0, singleShot=True)
        self._runlater.timeout.connect(self._runNextSession)

    def workingDirectory(self):
        return self._cwd

    def setWorkingDirectory(self, cwd):
        self._cwd = unicode(cwd)

    def isBusy(self):
        return bool(self._sessqueue)

    def _enqueueSession(self, sess):
        self._sessqueue.append(sess)
        if len(self._sessqueue) == 1:
            self.busyChanged.emit(self.isBusy())
            # make sure no command signals emitted in the current context
            self._runlater.start()

    def _dequeueSession(self, sess):
        # TODO: can't sessqueue.pop(0) due to incrementBusyCount hack
        self._sessqueue.remove(sess)
        if self._sessqueue:
            # make sure client can receive commandFinished before next session
            self._runlater.start()
        else:
            self._runlater.stop()
            self.busyChanged.emit(self.isBusy())

    def runCommand(self, cmdline, parent=None, display=None, worker=None):
        """Executes a single Mercurial command asynchronously and returns
        new CmdSession object"""
        return self.runCommandSequence([cmdline], parent=parent,
                                       display=display, worker=worker)

    def runCommandSequence(self, cmdlines, parent=None, display=None,
                           worker=None):
        """Executes a series of Mercurial commands asynchronously and returns
        new CmdSession object which will provide notification signals.

        CmdSession object will be disowned on command finished, even if parent
        is specified.

        If one of the preceding command exits with non-zero status, the
        following commands won't be executed.
        """
        if self._cwd:
            # TODO: pass to CmdSession so that CmdProc can use it directly
            cmdlines = [['--cwd', self._cwd] + list(xs) for xs in cmdlines]
        useproc = worker == 'proc'
        if not parent:
            parent = self
        sess = CmdSession(cmdlines, parent, display, useproc)
        sess.commandFinished.connect(self._onCommandFinished)
        sess.outputReceived.connect(self.outputReceived)
        sess.progressReceived.connect(self.progressReceived)
        self._enqueueSession(sess)
        return sess

    def abortCommands(self):
        """Abort running and queued commands; all command sessions will emit
        commandFinished in order"""
        for sess in self._sessqueue[:]:
            sess.abort()

    @pyqtSlot()
    def _runNextSession(self):
        sess = self._sessqueue[0]
        sess.run()

    @pyqtSlot()
    def _onCommandFinished(self):
        sess = self._sessqueue[0]
        if isinstance(self.sender(), CmdSession):  # avoid bug of PyQt 4.7.3
            assert sess is self.sender()
        sess.setParent(None)
        self._dequeueSession(sess)
