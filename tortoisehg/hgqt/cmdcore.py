# cmdcore.py - run Mercurial commands in a separate thread or process
#
# Copyright 2010 Yuki KODAMA <endflow.net@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import os, re, signal, struct, sys, time

from PyQt4.QtCore import QIODevice, QObject, QProcess, QTimer
from PyQt4.QtCore import pyqtSignal, pyqtSlot

from mercurial import util

from tortoisehg.util import hglib, paths, pipeui
from tortoisehg.hgqt.i18n import _
from tortoisehg.hgqt import thread

# TODO: should be moved from thread once CmdThread is superseded by CmdServer
ProgressMessage = thread.ProgressMessage

class UiHandler(QObject):
    """Interface to handle user interaction of Mercurial commands"""

    NoInput = 0
    TextInput = 1
    PasswordInput = 2
    ChoiceInput = 3

    def setPrompt(self, text, mode, default=None):
        pass

    def getLineInput(self):
        # '' to use default; None to abort
        return ''


def _createDefaultUiHandler(uiparent):
    if uiparent is None:
        return UiHandler()
    # this makes layering violation but is handy to create GUI handler by
    # default.  nobody would want to write
    #   uihandler = cmdui.InteractiveUiHandler(self)
    #   cmdagent.runCommand(..., uihandler)
    # in place of
    #   cmdagent.runCommand(..., self)
    from tortoisehg.hgqt import cmdui
    return cmdui.InteractiveUiHandler(None, uiparent)


class CmdWorker(QObject):
    """Back-end service to run Mercurial commands"""

    # If worker has permanent service, serviceState() should be overridden
    # to represent the availability of the service.  NoService denotes that
    # it can run command or quit immediately.
    NoService = 0
    Starting = 1
    Ready = 2
    Stopping = 3
    Restarting = 4
    NotRunning = 5

    serviceStateChanged = pyqtSignal(int)
    commandFinished = pyqtSignal(int)
    outputReceived = pyqtSignal(unicode, unicode)
    progressReceived = pyqtSignal(ProgressMessage)

    def serviceState(self):
        return CmdWorker.NoService
    def startService(self):
        # NotRunning->Starting; Stopping->Restarting->Starting; *->*
        pass
    def stopService(self):
        # {Starting,Ready,Restarting}->Stopping; *->*
        pass
    def startCommand(self, cmdline, uihandler):
        raise NotImplementedError
    def abortCommand(self):
        raise NotImplementedError
    def isCommandRunning(self):
        raise NotImplementedError


_localprocexts = [
    'tortoisehg.util.partialcommit',
    'tortoisehg.util.pipeui',
    ]

if os.name == 'nt':
    # to translate WM_CLOSE posted by QProcess.terminate()
    _localprocexts.append('tortoisehg.util.win32ill')

    def _interruptproc(proc):
        proc.terminate()

else:
    def _interruptproc(proc):
        os.kill(int(proc.pid()), signal.SIGINT)

def _fixprocenv(proc):
    env = os.environ.copy()
    if not getattr(sys, 'frozen', False):
        # make sure hg process can look up our modules
        env['PYTHONPATH'] = (paths.get_prog_root() + os.pathsep
                             + env.get('PYTHONPATH', ''))
    # not using setProcessEnvironment() for compatibility with PyQt 4.6
    proc.setEnvironment([hglib.tounicode('%s=%s' % p) for p in env.iteritems()])

def _proccmdline(exts):
    cmdline = map(hglib.tounicode, paths.get_hg_command())
    for e in exts:
        cmdline.extend(('--config', 'extensions.%s=' % e))
    return cmdline


class CmdProc(CmdWorker):
    'Run mercurial command in separate process'

    def __init__(self, parent=None, cwd=None):
        super(CmdProc, self).__init__(parent)
        self._proc = proc = QProcess(self)
        _fixprocenv(proc)
        if cwd:
            proc.setWorkingDirectory(cwd)
        proc.finished.connect(self.commandFinished)
        proc.readyReadStandardOutput.connect(self._stdout)
        proc.readyReadStandardError.connect(self._stderr)
        proc.error.connect(self._handleerror)

    def startCommand(self, cmdline, uihandler):
        fullcmdline = _proccmdline(_localprocexts)
        fullcmdline.extend(cmdline)
        self._proc.start(fullcmdline[0], fullcmdline[1:], QIODevice.ReadOnly)

    def abortCommand(self):
        if not self.isCommandRunning():
            return
        _interruptproc(self._proc)

    def isCommandRunning(self):
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
        self._processRead(data, '')

    def _stderr(self):
        data = self._proc.readAllStandardError().data()
        self._processRead(data, 'ui.error')

    def _processRead(self, fulldata, defaultlabel):
        for data in pipeui.splitmsgs(fulldata):
            msg, label = pipeui.unpackmsg(data)
            msg = hglib.tounicode(msg)
            if 'ui.progress' in label.split():
                progress = ProgressMessage(*pipeui.unpackprogress(msg))
                self.progressReceived.emit(progress)
            else:
                self.outputReceived.emit(msg, label or defaultlabel)


class CmdServer(CmdWorker):
    """Run Mercurial commands in command server process"""

    def __init__(self, parent=None, cwd=None):
        super(CmdServer, self).__init__(parent)
        self._uihandler = None
        self._readchtable = self._idlechtable
        self._readq = []  # (ch, data or datasize), ...
        # deadline for arrival of hello message and immature data
        self._readtimer = QTimer(self, interval=5000, singleShot=True)
        self._readtimer.timeout.connect(self._onReadTimeout)

        self._proc = proc = QProcess(self)
        _fixprocenv(proc)
        if cwd:
            proc.setWorkingDirectory(cwd)
        proc.error.connect(self._onServiceError)
        proc.finished.connect(self._onServiceFinished)
        proc.setReadChannel(QProcess.StandardOutput)
        proc.readyRead.connect(self._onReadyRead)
        proc.readyReadStandardError.connect(self._onReadyReadError)
        self._servicestate = CmdWorker.NotRunning

    def serviceState(self):
        return self._servicestate

    def _changeServiceState(self, newstate):
        if self._servicestate == newstate:
            return
        self._servicestate = newstate
        self.serviceStateChanged.emit(newstate)

    def startService(self):
        if self._servicestate == CmdWorker.NotRunning:
            self._startService()
        elif self._servicestate == CmdWorker.Stopping:
            self._changeServiceState(CmdWorker.Restarting)

    def _startService(self):
        cmdline = _proccmdline(_localprocexts)
        cmdline.extend(['serve', '--cmdserver', 'pipe',
                        '--config', 'ui.interactive=True'])
        self._readchtable = self._hellochtable
        self._readtimer.start()
        self._changeServiceState(CmdWorker.Starting)
        self._proc.start(cmdline[0], cmdline[1:])

    def stopService(self):
        if self._servicestate in (CmdWorker.Starting, CmdWorker.Ready):
            self._stopService()
        elif self._servicestate == CmdWorker.Restarting:
            self._changeServiceState(CmdWorker.Stopping)

    def _stopService(self):
        self._changeServiceState(CmdWorker.Stopping)
        _interruptproc(self._proc)
        # make sure "serve" loop ends by EOF (necessary on Windows)
        self._proc.closeWriteChannel()

    def _emitError(self, msg):
        self.outputReceived.emit('cmdserver: %s\n' % msg, 'ui.error')

    @pyqtSlot(QProcess.ProcessError)
    def _onServiceError(self, error):
        self._emitError(self._proc.errorString())
        if error == QProcess.FailedToStart:
            self._onServiceFinished()

    @pyqtSlot()
    def _onServiceFinished(self):
        self._uihandler = None
        self._readchtable = self._idlechtable
        del self._readq[:]
        self._readtimer.stop()
        if self._servicestate == CmdWorker.Restarting:
            self._startService()
            return
        if self._servicestate != CmdWorker.Stopping:
            self._emitError(_('process exited unexpectedly with code %d')
                            % self._proc.exitCode())
        self._changeServiceState(CmdWorker.NotRunning)

    def isCommandRunning(self):
        return self._readchtable is self._runcommandchtable

    def startCommand(self, cmdline, uihandler):
        assert self._servicestate == CmdWorker.Ready
        assert not self.isCommandRunning()
        data = hglib.fromunicode('\0'.join(cmdline))
        self._uihandler = uihandler
        self._readchtable = self._runcommandchtable
        self._proc.write('runcommand\n')
        self._writeBlock(data)

    def abortCommand(self):
        if not self.isCommandRunning():
            return
        _interruptproc(self._proc)

    def _finishCommand(self, ret):
        self._uihandler = None
        self._readchtable = self._idlechtable
        self.commandFinished.emit(ret)

    def _writeBlock(self, data):
        self._proc.write(struct.pack('>I', len(data)))
        self._proc.write(data)

    @pyqtSlot()
    def _onReadyRead(self):
        proc = self._proc
        headersize = 5
        try:
            while True:
                header = str(proc.peek(headersize))
                if not header:
                    self._readtimer.stop()
                    break
                if len(header) < headersize:
                    self._readtimer.start()
                    break
                ch, datasize = struct.unpack('>cI', header)
                if ch in 'IL':
                    # input channel has no data
                    proc.read(headersize)
                    self._readq.append((ch, datasize))
                    continue
                if proc.bytesAvailable() < headersize + datasize:
                    self._readtimer.start()
                    break
                proc.read(headersize)
                data = str(proc.read(datasize))
                self._readq.append((ch, data))

            # don't do much things in readyRead slot for simplicity
            QTimer.singleShot(0, self._dispatchRead)
        except Exception:
            self.stopService()
            raise

    @pyqtSlot()
    def _onReadTimeout(self):
        startbytes = str(self._proc.peek(20))
        if startbytes:
            # data corruption because bad extension might write to stdout?
            self._emitError(_('timed out while reading: %r...') % startbytes)
        else:
            self._emitError(_('timed out waiting for message'))
        self.stopService()

    @pyqtSlot()
    def _dispatchRead(self):
        try:
            while self._readq:
                ch, dataorsize = self._readq.pop(0)
                try:
                    chfunc = self._readchtable[ch]
                except KeyError:
                    if not ch.isupper():
                        continue
                    self._emitError(_('unexpected response on required '
                                      'channel %r') % ch)
                    self.stopService()
                    return
                chfunc(self, dataorsize)
        except Exception:
            self.stopService()
            raise

    @pyqtSlot()
    def _onReadyReadError(self):
        fulldata = str(self._proc.readAllStandardError())
        for data in pipeui.splitmsgs(fulldata):
            msg, label = pipeui.unpackmsg(data)
            msg = hglib.tounicode(msg)
            self.outputReceived.emit(msg, label or 'ui.error')

    def _processHello(self, data):
        try:
            fields = dict(l.split(':', 1) for l in data.splitlines())
            capabilities = fields['capabilities'].split()
        except (KeyError, ValueError):
            self._emitError(_('invalid "hello" message: %r') % data)
            self.stopService()
            return
        if 'runcommand' not in capabilities:
            self._emitError(_('no "runcommand" capability'))
            self.stopService()
            return
        self._readchtable = self._idlechtable
        self._changeServiceState(CmdWorker.Ready)

    def _processOutput(self, data):
        msg, label = pipeui.unpackmsg(data)
        msg = hglib.tounicode(msg)
        labelset = label.split()
        if 'ui.progress' in labelset:
            progress = ProgressMessage(*pipeui.unpackprogress(msg))
            self.progressReceived.emit(progress)
        elif 'ui.prompt' in labelset:
            if 'ui.getpass' in labelset:
                mode = UiHandler.PasswordInput
            elif 'ui.promptchoice' in labelset:
                mode = UiHandler.ChoiceInput
            else:
                mode = UiHandler.TextInput
            prompt, default = pipeui.unpackprompt(msg)
            self._uihandler.setPrompt(prompt, mode, default)
        else:
            self.outputReceived.emit(msg, label)

    def _processCommandResult(self, data):
        try:
            ret, = struct.unpack('>i', data)
            # command server returns raw result code in hg<3.0 (5d4606bec54c)
            ret &= 255
        except struct.error:
            self._emitError(_('corrupted command result: %r') % data)
            self.stopService()
            return
        self._finishCommand(ret)

    def _processLineRequest(self, size):
        text = self._uihandler.getLineInput()
        if text is None:
            self._writeBlock('')
            return
        data = hglib.fromunicode(text) + '\n'
        for start in xrange(0, len(data), size):
            self._writeBlock(data[start:start + size])

    _idlechtable = {
        'o': _processOutput,
        'e': _processOutput,
        }

    _hellochtable = {
        'o': _processHello,
        'e': _processOutput,
        }

    _runcommandchtable = {
        'o': _processOutput,
        'e': _processOutput,
        'r': _processCommandResult,
        # implement 'I' (data input) channel if necessary
        'L': _processLineRequest,
        }


_workertypes = {
    'thread': thread.CmdThread,
    'proc': CmdProc,
    'server': CmdServer,
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
    # in order to receive only notification messages of session state, use
    # "controlMessage"; otherwise use "outputReceived"
    controlMessage = pyqtSignal(unicode)
    outputReceived = pyqtSignal(unicode, unicode)
    progressReceived = pyqtSignal(ProgressMessage)

    def __init__(self, cmdlines, uihandler, parent=None):
        super(CmdSession, self).__init__(parent)
        self._uihandler = uihandler
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
        if self._worker or self._qnextp >= len(self._queue):
            return
        self._connectWorker(worker)
        if worker.serviceState() in (CmdWorker.NoService, CmdWorker.Ready):
            self._runNext()

    def abort(self):
        '''Cancel running Mercurial command'''
        if self.isRunning():
            self._worker.abortCommand()
            self._qnextp = len(self._queue)
            self._abortbyuser = True
        elif not self.isFinished():
            self._abortbyuser = True
            # -1 instead of 255 for compatibility with CmdThread
            self._finish(-1)

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
        return bool(self._worker) and self._qnextp > 0

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
        worker.serviceStateChanged.connect(self._onWorkerStateChanged)
        worker.commandFinished.connect(self._onCommandFinished)
        worker.outputReceived.connect(self.outputReceived)
        worker.outputReceived.connect(self._captureOutput)
        worker.progressReceived.connect(self.progressReceived)

    def _disconnectWorker(self):
        worker = self._worker
        if not worker:
            return
        worker.serviceStateChanged.disconnect(self._onWorkerStateChanged)
        worker.commandFinished.disconnect(self._onCommandFinished)
        worker.outputReceived.disconnect(self.outputReceived)
        worker.outputReceived.disconnect(self._captureOutput)
        worker.progressReceived.disconnect(self.progressReceived)
        self._worker = None

    def _emitControlMessage(self, msg):
        self.controlMessage.emit(msg)
        self.outputReceived.emit(msg + '\n', 'control')

    def _runNext(self):
        cmdline = self._queue[self._qnextp]
        self._qnextp += 1

        self._abortbyuser = False
        del self._erroroutputs[:]
        del self._warningoutputs[:]
        self._worker.startCommand(cmdline, self._uihandler)
        self._emitControlMessage('% hg ' + _prettifycmdline(cmdline))

    def _finish(self, ret):
        self._qnextp = len(self._queue)
        self._disconnectWorker()
        self._exitcode = ret
        self.commandFinished.emit(ret)

    ### Signal Handlers ###

    @pyqtSlot(int)
    def _onWorkerStateChanged(self, state):
        if state == CmdWorker.Ready:
            assert self._qnextp == 0
            self._runNext()
        elif state == CmdWorker.NotRunning:
            # unexpected end of command execution
            self._finish(-1)

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
        self._emitControlMessage(msg % time.asctime())

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
    return CmdSession([], UiHandler())


class CmdAgent(QObject):
    """Manage requests of Mercurial commands"""

    serviceStopped = pyqtSignal()
    busyChanged = pyqtSignal(bool)

    # Signal forwarding:
    #   worker ---- agent   commandFinished:  session (= last one of worker)
    #      \         /      outputReceived:   worker + session
    #        session        progressReceived: worker (= session)
    #
    # Inactive session is not started by the agent, so agent.commandFinished
    # won't be emitted when waiting session is aborted.
    commandFinished = pyqtSignal(CmdSession)
    outputReceived = pyqtSignal(unicode, unicode)
    progressReceived = pyqtSignal(ProgressMessage)

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

    def isServiceRunning(self):
        stoppedstates = (CmdWorker.NoService, CmdWorker.NotRunning)
        return util.any(worker.serviceState() not in stoppedstates
                        for worker in self._workers.itervalues())

    def stopService(self):
        """Shut down back-end services so that this can be deleted safely or
        reconfigured; serviceStopped will be emitted asynchronously"""
        for worker in self._workers.itervalues():
            worker.stopService()

    @pyqtSlot()
    def _tryEmitServiceStopped(self):
        if not self.isServiceRunning():
            self.serviceStopped.emit()

    def isBusy(self):
        return bool(self._sessqueue)

    def _enqueueSession(self, sess, workername):
        self._sessqueue.append((sess, workername))
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

    def _cleanupWaitingSession(self):
        for i in reversed(xrange(1, len(self._sessqueue))):
            sess, _workername = self._sessqueue[i]
            if sess.isFinished():
                del self._sessqueue[i]
                sess.setParent(None)

    def runCommand(self, cmdline, uihandler=None, worker=None):
        """Executes a single Mercurial command asynchronously and returns
        new CmdSession object"""
        return self.runCommandSequence([cmdline], uihandler, worker=worker)

    def runCommandSequence(self, cmdlines, uihandler=None, worker=None):
        """Executes a series of Mercurial commands asynchronously and returns
        new CmdSession object which will provide notification signals.

        The optional uihandler is the call-back of user-interaction requests.
        If uihandler does not implement UiHandler interface, it will be used
        as the parent widget of the default InteractiveUiHandler.  If uihandler
        is None, no interactive prompt will be displayed.

        CmdSession object will be disowned on command finished.  The specified
        uihandler is unrelated to the lifetime of CmdSession object.

        If one of the preceding command exits with non-zero status, the
        following commands won't be executed.
        """
        if worker and worker not in _workertypes:
            raise ValueError('invalid worker type: %r' % worker)
        if not worker:
            worker = self._defaultWorkerName()
        if not isinstance(uihandler, UiHandler):
            uihandler = _createDefaultUiHandler(uihandler)
        sess = CmdSession(cmdlines, uihandler, self)
        sess.commandFinished.connect(self._onCommandFinished)
        sess.controlMessage.connect(self._forwardControlMessage)
        self._enqueueSession(sess, worker)
        return sess

    def abortCommands(self):
        """Abort running and queued commands; all command sessions will emit
        commandFinished"""
        for sess, _workername in self._sessqueue[:]:
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
            assert not worker.isCommandRunning() or thread.HAVE_QTBUG_30251
            return worker
        self._ui.debug("creating cmdworker '%s'\n" % name)
        self._workers[name] = worker = _workertypes[name](self, self._cwd)
        worker.serviceStateChanged.connect(self._tryEmitServiceStopped)
        worker.outputReceived.connect(self.outputReceived)
        worker.progressReceived.connect(self.progressReceived)
        return worker

    @pyqtSlot()
    def _runNextSession(self):
        sess, workername = self._sessqueue[0]
        worker = self._prepareWorker(workername)
        sess.run(worker)
        # start after connected to sess so that it can receive immediate error
        worker.startService()

    @pyqtSlot()
    def _onCommandFinished(self):
        sess, _workername = self._sessqueue[0]
        if not sess.isFinished():
            # waiting session is aborted, just delete it
            self._cleanupWaitingSession()
            return
        self._dequeueSession()
        self.commandFinished.emit(sess)
        sess.setParent(None)

    @pyqtSlot(unicode)
    def _forwardControlMessage(self, msg):
        self.outputReceived.emit(msg + '\n', 'control')
