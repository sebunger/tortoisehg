# cmdcore.py - run Mercurial commands in a separate thread or process
#
# Copyright 2010 Yuki KODAMA <endflow.net@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import os, re, signal, time, weakref

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

    def __init__(self, parent=None, cwd=None):
        super(CmdProc, self).__init__(parent)
        self._proc = proc = QProcess(self)
        if cwd:
            proc.setWorkingDirectory(cwd)
        proc.started.connect(self.started)
        proc.finished.connect(self.commandFinished)
        proc.readyReadStandardOutput.connect(self._stdout)
        proc.readyReadStandardError.connect(self._stderr)
        proc.error.connect(self._handleerror)

    def startCommand(self, cmdline):
        fullcmdline = map(hglib.tounicode, paths.get_hg_command()) + cmdline
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

    def setUiParent(self, parent):
        # not interactive
        pass

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


_workertypes = {
    'thread': thread.CmdThread,
    'proc': CmdProc,
    }


_urlpassre = re.compile(r'^([a-zA-Z0-9+.\-]+://[^:@/]*):[^@/]+@')

def _reprcmdarg(arg):
    arg = _urlpassre.sub(r'\1:***@', arg)
    arg = arg.replace('\n', '^M')

    # only for display; no use to construct command string for os.system()
    if not arg or ' ' in arg or '\\' in arg or '"' in arg:
        return '"%s"' % arg.replace('"', '\\"')
    else:
        return arg

def _prettifycmdline(cmdline):
    r"""Build pretty command-line string for display

    >>> _prettifycmdline(['log', 'foo\\bar', '', 'foo bar', 'foo"bar'])
    'log "foo\\bar" "" "foo bar" "foo\\"bar"'
    >>> _prettifycmdline(['log', '--template', '{node}\n'])
    'log --template {node}^M'

    mask password in url-like string:

    >>> _prettifycmdline(['push', 'http://foo123:bar456@example.org/'])
    'push http://foo123:***@example.org/'
    >>> _prettifycmdline(['clone', 'svn+http://:bar@example.org:8080/trunk/'])
    'clone svn+http://:***@example.org:8080/trunk/'
    """
    return ' '.join(_reprcmdarg(e) for e in cmdline)

class CmdSession(QObject):
    """Run Mercurial commands in a background thread or process"""

    commandFinished = pyqtSignal(int)

    outputReceived = pyqtSignal(unicode, unicode)
    progressReceived = pyqtSignal(unicode, object, unicode, unicode, object)

    def __init__(self, cmdlines, parent=None):
        super(CmdSession, self).__init__(parent)

        self._worker = None
        self._queue = list(cmdlines)
        self._qnextp = 0
        self._abortbyuser = False
        self._erroroutputs = []
        self._warningoutputs = []
        self._exitcode = 0
        if not cmdlines:
            # assumes null session is failure for convenience
            self._exitcode = -1

    ### Public Methods ###

    def run(self, worker):
        '''Execute Mercurial command'''
        if self.isRunning() or self._qnextp >= len(self._queue):
            return
        if self._abortbyuser:
            # -1 instead of 255 for compatibility with CmdThread
            self._finish(-1)
            return
        self._connectWorker(worker)
        self._runNext()

    def abort(self):
        '''Cancel running Mercurial command'''
        if self.isRunning():
            self._worker.abort()
            self._qnextp = len(self._queue)
            self._abortbyuser = True
        elif not self.isFinished():
            # don't abort immediately because this hasn't started yet
            self._abortbyuser = True

    def isAborted(self):
        """True if commands have finished by user abort"""
        return self.isFinished() and self._abortbyuser

    def isFinished(self):
        """True if all pending commands have finished or been aborted"""
        return self._qnextp >= len(self._queue) and not self.isRunning()

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

    def _connectWorker(self, worker):
        self._worker = worker
        worker.started.connect(self._onCommandStarted)
        worker.commandFinished.connect(self._onCommandFinished)
        worker.outputReceived.connect(self.outputReceived)
        worker.outputReceived.connect(self._captureOutput)
        worker.progressReceived.connect(self.progressReceived)

    def _disconnectWorker(self):
        worker = self._worker
        if not worker:
            return
        worker.started.disconnect(self._onCommandStarted)
        worker.commandFinished.disconnect(self._onCommandFinished)
        worker.outputReceived.disconnect(self.outputReceived)
        worker.outputReceived.disconnect(self._captureOutput)
        worker.progressReceived.disconnect(self.progressReceived)
        self._worker = None

    def _runNext(self):
        cmdline = self._queue[self._qnextp]
        self._qnextp += 1

        self._abortbyuser = False
        del self._erroroutputs[:]
        del self._warningoutputs[:]
        self._worker.startCommand(cmdline)

    def _finish(self, ret):
        self._qnextp = len(self._queue)
        self._disconnectWorker()
        self._exitcode = ret
        self.commandFinished.emit(ret)

    ### Signal Handlers ###

    @pyqtSlot()
    def _onCommandStarted(self):
        cmd = '%% hg %s\n' % _prettifycmdline(self._queue[self._qnextp - 1])
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

        if ret != 0 or self._qnextp >= len(self._queue):
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

    exitCode() is -1 so that the command dialog can finish with error status
    if nothing executed.

    >>> sess = nullCmdSession()
    >>> sess.isFinished(), sess.isRunning(), sess.isAborted(), sess.exitCode()
    (True, False, False, -1)
    >>> sess.abort()  # should not change flags
    >>> sess.isFinished(), sess.isRunning(), sess.isAborted(), sess.exitCode()
    (True, False, False, -1)
    """
    return CmdSession([])


class CmdAgent(QObject):
    """Manage requests of Mercurial commands"""

    busyChanged = pyqtSignal(bool)
    commandFinished = pyqtSignal(CmdSession)
    outputReceived = pyqtSignal(unicode, unicode)
    progressReceived = pyqtSignal(unicode, object, unicode, unicode, object)

    # isBusy() is False when the last commandFinished is emitted, but you
    # shouldn't rely on the emission order of busyChanged and commandFinished.

    def __init__(self, ui, parent=None):
        super(CmdAgent, self).__init__(parent)
        self._ui = ui
        self._cwd = None
        self._workers = {}
        self._sessqueue = []  # [active, waiting...]
        self._runlater = QTimer(self, interval=0, singleShot=True)
        self._runlater.timeout.connect(self._runNextSession)

    def workingDirectory(self):
        return self._cwd

    def setWorkingDirectory(self, cwd):
        if self._workers:
            raise RuntimeError('cannot change working directory after run')
        self._cwd = unicode(cwd)

    def isBusy(self):
        return bool(self._sessqueue)

    def _enqueueSession(self, sess, workername, parentref):
        self._sessqueue.append((sess, workername, parentref))
        if len(self._sessqueue) == 1:
            self.busyChanged.emit(self.isBusy())
            # make sure no command signals emitted in the current context
            self._runlater.start()

    def _dequeueSession(self):
        del self._sessqueue[0]
        if self._sessqueue:
            # make sure client can receive commandFinished before next session
            self._runlater.start()
        else:
            self._runlater.stop()
            self.busyChanged.emit(self.isBusy())

    def runCommand(self, cmdline, parent=None, worker=None):
        """Executes a single Mercurial command asynchronously and returns
        new CmdSession object"""
        return self.runCommandSequence([cmdline], parent=parent, worker=worker)

    def runCommandSequence(self, cmdlines, parent=None, worker=None):
        """Executes a series of Mercurial commands asynchronously and returns
        new CmdSession object which will provide notification signals.

        CmdSession object will be disowned on command finished.  The specified
        parent is unrelated to the lifetime of CmdSession object.  It is used
        as the parent widget of the interactive GUI prompt.

        If one of the preceding command exits with non-zero status, the
        following commands won't be executed.
        """
        if worker and worker not in _workertypes:
            raise ValueError('invalid worker type: %r' % worker)
        if not worker:
            worker = self._defaultWorkerName()
        sess = CmdSession(cmdlines, self)
        sess.commandFinished.connect(self._onCommandFinished)
        sess.outputReceived.connect(self.outputReceived)
        sess.progressReceived.connect(self.progressReceived)
        self._enqueueSession(sess, worker, parent and weakref.ref(parent))
        return sess

    def abortCommands(self):
        """Abort running and queued commands; all command sessions will emit
        commandFinished in order"""
        for sess, _workername, _parentref in self._sessqueue[:]:
            sess.abort()

    def _defaultWorkerName(self):
        # hidden config for debugging or testing experimental worker
        name = self._ui.config('tortoisehg', 'cmdworker', 'thread')
        if name not in _workertypes:
            self.outputReceived.emit(_("ignoring invalid cmdworker '%s'\n")
                                     % hglib.tounicode(name), 'ui.warning')
            return 'thread'
        return name

    def _prepareWorker(self, name):
        worker = self._workers.get(name)
        if worker:
            assert not worker.isRunning() or thread.HAVE_QTBUG_30251
            return worker
        self._workers[name] = worker = _workertypes[name](self, self._cwd)
        return worker

    @pyqtSlot()
    def _runNextSession(self):
        sess, workername, parentref = self._sessqueue[0]
        worker = self._prepareWorker(workername)
        worker.setUiParent(parentref and parentref())
        sess.run(worker)

    @pyqtSlot()
    def _onCommandFinished(self):
        sess, _workername, _parentref = self._sessqueue[0]
        if isinstance(self.sender(), CmdSession):  # avoid bug of PyQt 4.7.3
            assert sess is self.sender()
        self._dequeueSession()
        self.commandFinished.emit(sess)
        sess.setParent(None)
