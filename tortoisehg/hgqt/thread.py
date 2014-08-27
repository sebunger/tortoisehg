# thread.py - A separate thread to run Mercurial commands
#
# Copyright 2009 Steve Borho <steve@borho.org>
# Copyright 2010 Yuki KODAMA <endflow.net@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import Queue

from PyQt4.QtCore import *

from mercurial import util
from mercurial import ui as uimod

from tortoisehg.util import thread2, hgdispatch, hglib
from tortoisehg.hgqt.i18n import _, localgettext

local = localgettext()

class DataWrapper(object):
    def __init__(self, data):
        self.data = data

# reference as cmdcore.ProgressMessage instead of thread.ProgressMessage
class ProgressMessage(tuple):
    __slots__ = ()

    def __new__(cls, topic, pos, item='', unit='', total=None):
        return tuple.__new__(cls, (topic, pos, item, unit, total))

    @property
    def topic(self):
        return self[0]  # unicode
    @property
    def pos(self):
        return self[1]  # int or None
    @property
    def item(self):
        return self[2]  # unicode
    @property
    def unit(self):
        return self[3]  # unicode
    @property
    def total(self):
        return self[4]  # int or None

    def __repr__(self):
        names = ('topic', 'pos', 'item', 'unit', 'total')
        fields = ('%s=%r' % (n, v) for n, v in zip(names, self))
        return '%s(%s)' % (self.__class__.__name__, ', '.join(fields))


class UiSignal(QObject):
    writeSignal = pyqtSignal(QByteArray, QString)
    progressSignal = pyqtSignal(QString, object, QString, QString, object)
    interactSignal = pyqtSignal(DataWrapper)

    def __init__(self, responseq):
        QObject.__init__(self)
        self.responseq = responseq

    def write(self, *args, **opts):
        msg = QByteArray(''.join(args))
        label = hglib.tounicode(opts.get('label', ''))
        self.writeSignal.emit(msg, label)

    def write_err(self, *args, **opts):
        msg = QByteArray(''.join(args))
        label = hglib.tounicode(opts.get('label', ''))
        self.writeSignal.emit(msg, label or 'ui.error')

    def prompt(self, msg, default):
        try:
            r = self._waitresponse(msg, False, None, None)
            if r is None:
                raise EOFError
            if not r:
                return default
            return r
        except EOFError:
            raise util.Abort(local._('response expected'))

    def promptchoice(self, prompt, default):
        try:
            r = self._waitresponse(prompt, False, True, default)
            if r is None:
                raise EOFError
            return r
        except EOFError:
            raise util.Abort(local._('response expected'))

    def getpass(self, prompt, default):
        r = self._waitresponse(prompt, True, None, default)
        if r is None:
            raise util.Abort(local._('response expected'))
        return r

    def _waitresponse(self, msg, password, choices, default):
        """Request interaction with GUI and wait response from it"""
        data = DataWrapper((msg, password, choices, default))
        self.interactSignal.emit(data)
        # await response
        return self.responseq.get(True)

    def progress(self, topic, pos, item, unit, total):
        topic = hglib.tounicode(topic or '')
        item = hglib.tounicode(item or '')
        unit = hglib.tounicode(unit or '')
        self.progressSignal.emit(topic, pos, item, unit, total)

class QtUi(uimod.ui):
    def __init__(self, src=None, responseq=None):
        super(QtUi, self).__init__(src)

        if src:
            self.sig = src.sig
        else:
            self.sig = UiSignal(responseq)

        self.setconfig('ui', 'interactive', 'on')
        self.setconfig('progress', 'disable', 'True')

    def plain(self, feature=None):
        return feature not in ('alias', 'i18n')

    def write(self, *args, **opts):
        if self._buffers:
            self._buffers[-1].extend([str(a) for a in args])
        else:
            self.sig.write(*args, **opts)

    def write_err(self, *args, **opts):
        self.sig.write_err(*args, **opts)

    def label(self, msg, label):
        return msg

    def flush(self):
        pass

    def prompt(self, msg, default='y'):
        if not self.interactive(): return default
        return self.sig.prompt(msg, default)

    def promptchoice(self, prompt, default=0):
        if not self.interactive(): return default
        return self.sig.promptchoice(prompt, default)

    def getpass(self, prompt=None, default=None):
        return self.sig.getpass(prompt or _('password: '), default)

    def progress(self, topic, pos, item='', unit='', total=None):
        return self.sig.progress(topic, pos, item, unit, total)


# QThread.finished is raised before running and finished attributes are set
HAVE_QTBUG_30251 = 0x40800 <= QT_VERSION < 0x40805

class CmdThread(QThread):
    """Run an Mercurial command in a background thread, implies output
    is being sent to a rendered text buffer interactively and requests
    for feedback from Mercurial can be handled by the user via dialog
    windows.
    """

    serviceStateChanged = pyqtSignal(int)

    # (msg=str, label=str)
    outputReceived = pyqtSignal(QString, QString)

    progressReceived = pyqtSignal(ProgressMessage)

    # result: -1 - command is incomplete, possibly exited with exception
    #          0 - command is finished successfully
    #          others - return code of command
    commandFinished = pyqtSignal(int)

    def __init__(self, parent=None, cwd=None):
        super(CmdThread, self).__init__(parent)

        self.cmdline = None
        self._cwd = hglib.fromunicode(cwd)
        self._uihandler = None
        self.ret = -1
        self.responseq = Queue.Queue()
        self.topics = {}
        self.curstrs = QStringList()
        self.curlabel = None
        self.timer = QTimer(self, interval=100)
        self.timer.timeout.connect(self.flush)
        self.started.connect(self.timer.start)
        self.finished.connect(self.thread_finished)

    def serviceState(self):
        return 0  # NoService

    def startService(self):
        pass

    def stopService(self):
        pass

    def startCommand(self, cmdline, uihandler):
        assert not self.isCommandRunning() or HAVE_QTBUG_30251
        self.cmdline = map(hglib.fromunicode, cmdline)
        self._uihandler = uihandler
        if self._cwd:
            self.cmdline[0:0] = ['--cwd', self._cwd]
        self.start()

    def abortCommand(self):
        if self.isCommandRunning() and hasattr(self, 'thread_id'):
            try:
                thread2._async_raise(self.thread_id, KeyboardInterrupt)
            except ValueError:
                pass

    def isCommandRunning(self):
        return self.isRunning()

    @pyqtSlot()
    def thread_finished(self):
        self.timer.stop()
        self.flush()
        self._uihandler = None
        self.commandFinished.emit(self.ret)

    def flush(self):
        if self.curlabel is not None:
            self.outputReceived.emit(self.curstrs.join(''), self.curlabel)
        self.curlabel = None
        if self.timer.isActive():
            keys = self.topics.keys()
            for topic in keys:
                pos, item, unit, total = self.topics[topic]
                progress = ProgressMessage(unicode(topic), pos, unicode(item),
                                           unicode(unit), total)
                self.progressReceived.emit(progress)
                if pos is None:
                    del self.topics[topic]
        else:
            # Close all progress bars
            for topic in self.topics:
                progress = ProgressMessage(unicode(topic), None)
                self.progressReceived.emit(progress)
            self.topics = {}

    @pyqtSlot(QByteArray, QString)
    def output_handler(self, msg, label):
        if self._uihandler.writeOutput(msg, unicode(label)) >= 0:
            return
        msg = hglib.tounicode(str(msg))
        if label == self.curlabel:
            self.curstrs.append(msg)
        else:
            if self.curlabel is not None:
                self.outputReceived.emit(self.curstrs.join(''), self.curlabel)
            self.curstrs = QStringList(msg)
            self.curlabel = label

    @pyqtSlot(QString, object, QString, QString, object)
    def progress_handler(self, topic, pos, item, unit, total):
        self.topics[topic] = (pos, item, unit, total)

    @pyqtSlot(DataWrapper)
    def interact_handler(self, wrapper):
        prompt, password, choices, default = wrapper.data
        prompt = hglib.tounicode(prompt)
        uihandler = self._uihandler
        if choices:
            parts = prompt.split('$$')
            resps = [p[p.index('&') + 1].lower() for p in parts[1:]]
            uihandler.setPrompt(prompt, uihandler.ChoiceInput, resps[default])
            r = uihandler.getLineInput()
            if r is None:
                self.responseq.put(None)
            elif not r:
                self.responseq.put(default)
            else:
                self.responseq.put(resps.index(r))
        else:
            mode = password and uihandler.PasswordInput \
                             or uihandler.TextInput
            uihandler.setPrompt(prompt, mode)
            text = hglib.fromunicode(uihandler.getLineInput())
            self.responseq.put(text)

    def run(self):
        ui = QtUi(responseq=self.responseq)
        ui.sig.writeSignal.connect(self.output_handler,
                Qt.QueuedConnection)
        ui.sig.progressSignal.connect(self.progress_handler,
                Qt.QueuedConnection)
        ui.sig.interactSignal.connect(self.interact_handler,
                Qt.QueuedConnection)

        try:
            # save thread id in order to terminate by KeyboardInterrupt
            self.thread_id = int(QThread.currentThreadId())

            # disable worker because it only works in main thread:
            #   signal.signal(signal.SIGINT, signal.SIG_IGN)
            #   ValueError: signal only works in main thread
            ui.setconfig('worker', 'numcpus', 1)
            self.ret = 255
            self.ret = hgdispatch.dispatch(ui, self.cmdline)
        except Exception, inst:
            ui.write_err(str(inst) + '\n', label='ui.error')
            raise
        except KeyboardInterrupt:
            self.ret = -1
