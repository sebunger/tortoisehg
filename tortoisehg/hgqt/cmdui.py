# cmdui.py - A widget to execute Mercurial command for TortoiseHg
#
# Copyright 2010 Yuki KODAMA <endflow.net@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.Qsci import QsciScintilla

from tortoisehg.util import hglib
from tortoisehg.hgqt.i18n import _, localgettext
from tortoisehg.hgqt import cmdcore, qtlib, qscilib

local = localgettext()

def startProgress(topic, status):
    topic, item, pos, total, unit = topic, '...', status, None, ''
    return (topic, pos, item, unit, total)

def stopProgress(topic):
    topic, item, pos, total, unit = topic, '', None, None, ''
    return (topic, pos, item, unit, total)

class ProgressMonitor(QWidget):
    'Progress bar for use in workbench status bar'
    def __init__(self, topic, parent):
        super(ProgressMonitor, self).__init__(parent)

        hbox = QHBoxLayout()
        hbox.setContentsMargins(*(0,)*4)
        self.setLayout(hbox)
        self.idle = False

        self.pbar = QProgressBar()
        self.pbar.setTextVisible(False)
        self.pbar.setMinimum(0)
        hbox.addWidget(self.pbar)

        self.topic = QLabel(topic)
        hbox.addWidget(self.topic, 0)

        self.status = QLabel()
        hbox.addWidget(self.status, 1)

        self.pbar.setMaximum(100)
        self.pbar.reset()
        self.status.setText('')

    def clear(self):
        self.pbar.setMinimum(0)
        self.pbar.setMaximum(100)
        self.pbar.setValue(100)
        self.status.setText('')
        self.idle = True

    def setcounts(self, cur, max):
        # cur and max may exceed INT_MAX, which confuses QProgressBar
        assert max != 0
        self.pbar.setMaximum(100)
        self.pbar.setValue(int(cur * 100 / max))

    def unknown(self):
        self.pbar.setMinimum(0)
        self.pbar.setMaximum(0)


class ThgStatusBar(QStatusBar):
    linkActivated = pyqtSignal(QString)

    def __init__(self, parent=None):
        QStatusBar.__init__(self, parent)
        self.topics = {}
        self.lbl = QLabel()
        self.lbl.linkActivated.connect(self.linkActivated)
        self.addWidget(self.lbl)
        self.setStyleSheet('QStatusBar::item { border: none }')

    @pyqtSlot(unicode)
    def showMessage(self, ustr, error=False):
        self.lbl.setText(ustr)
        if error:
            self.lbl.setStyleSheet('QLabel { color: red }')
        else:
            self.lbl.setStyleSheet('')

    def clear(self):
        keys = self.topics.keys()
        for key in keys:
            pm = self.topics[key]
            self.removeWidget(pm)
            del self.topics[key]

    @pyqtSlot(QString, object, QString, QString, object)
    def progress(self, topic, pos, item, unit, total, root=None):
        'Progress signal received from repowidget'
        # topic is current operation
        # pos is the current numeric position (revision, bytes)
        # item is a non-numeric marker of current position (current file)
        # unit is a string label
        # total is the highest expected pos
        #
        # All topics should be marked closed by setting pos to None
        if root:
            key = (root, topic)
        else:
            key = topic
        if pos is None or (not pos and not total):
            if key in self.topics:
                pm = self.topics[key]
                self.removeWidget(pm)
                del self.topics[key]
            return
        if key not in self.topics:
            pm = ProgressMonitor(topic, self)
            pm.setMaximumHeight(self.lbl.sizeHint().height())
            self.addWidget(pm)
            self.topics[key] = pm
        else:
            pm = self.topics[key]
        if total:
            fmt = '%s / %s ' % (unicode(pos), unicode(total))
            if unit:
                fmt += unit
            pm.status.setText(fmt)
            pm.setcounts(pos, total)
        else:
            if item:
                item = item[-30:]
            pm.status.setText('%s %s' % (unicode(pos), item))
            pm.unknown()

def updateStatusMessage(stbar, session):
    """Update status bar to show the status of the given session"""
    if not session.isFinished():
        stbar.showMessage(_('Running...'))
    elif session.isAborted():
        stbar.showMessage(_('Terminated by user'))
    elif session.exitCode() == 0:
        stbar.showMessage(_('Finished'))
    else:
        stbar.showMessage(_('Failed!'), True)


class Core(QObject):
    """Core functionality for running Mercurial command.
    Do not attempt to instantiate and use this directly.
    """

    commandStarted = pyqtSignal()
    commandFinished = pyqtSignal(int)
    commandCanceling = pyqtSignal()

    output = pyqtSignal(QString, QString)
    progress = pyqtSignal(QString, object, QString, QString, object)

    def __init__(self, logWindow, parent):
        super(Core, self).__init__(parent)

        self._agent = cmdcore.CmdAgent(self)
        self._session = cmdcore.nullCmdSession()
        self.rawoutlines = []
        self.stbar = None
        if logWindow:
            self.outputLog = LogWidget()
            self.outputLog.installEventFilter(qscilib.KeyPressInterceptor(self))
            self.output.connect(self.outputLog.appendLog)

    ### Public Methods ###

    def run(self, cmdline, *cmdlines, **opts):
        '''Execute or queue Mercurial command'''
        display = opts.get('display')
        worker = opts.get('useproc', False) and 'proc' or None
        ucmdlines = [map(hglib.tounicode, xs) for xs in (cmdline,) + cmdlines]
        udisplay = hglib.tounicode(display)
        sess = self._agent.runCommandSequence(ucmdlines, self,
                                              display=udisplay, worker=worker)
        sess.commandFinished.connect(self.onCommandFinished)
        sess.outputReceived.connect(self.onOutputReceived)
        sess.progressReceived.connect(self.onProgressReceived)
        self._session = sess
        # client widget assumes that the command starts immediately
        self.onCommandStarted()

    def cancel(self):
        '''Cancel running Mercurial command'''
        if self.running():
            self._session.abort()
            self.commandCanceling.emit()

    def running(self):
        # pending session is "running" in cmdui world
        return not self._session.isFinished()

    def rawoutput(self):
        return ''.join(self.rawoutlines)

    def setStbar(self, stbar):
        self.stbar = stbar

    ### Private Method ###

    def clearOutput(self):
        if hasattr(self, 'outputLog'):
            self.outputLog.clearLog()

    ### Signal Handlers ###

    def onCommandStarted(self):
        self.rawoutlines = []
        self.commandStarted.emit()
        if self.stbar:
            updateStatusMessage(self.stbar, self._session)

    @pyqtSlot(int)
    def onCommandFinished(self, ret):
        if self.stbar:
            updateStatusMessage(self.stbar, self._session)
        self.commandFinished.emit(ret)

    @pyqtSlot(QString, QString)
    def onOutputReceived(self, msg, label):
        if label != 'control':
            self.rawoutlines.append(hglib.fromunicode(msg, 'replace'))
        self.output.emit(msg, label)

    @pyqtSlot(QString, object, QString, QString, object)
    def onProgressReceived(self, topic, pos, item, unit, total):
        self.progress.emit(topic, pos, item, unit, total)
        if self.stbar:
            self.stbar.progress(topic, pos, item, unit, total)


class LogWidget(qscilib.ScintillaCompat):
    """Output log viewer"""

    def __init__(self, parent=None):
        super(LogWidget, self).__init__(parent)
        self.setReadOnly(True)
        self.setUtf8(True)
        self.setMarginWidth(1, 0)
        self.setWrapMode(QsciScintilla.WrapCharacter)
        self._initfont()
        self._initmarkers()
        qscilib.unbindConflictedKeys(self)

    def _initfont(self):
        tf = qtlib.getfont('fontoutputlog')
        tf.changed.connect(self.forwardFont)
        self.setFont(tf.font())

    @pyqtSlot(QFont)
    def forwardFont(self, font):
        self.setFont(font)

    def _initmarkers(self):
        self._markers = {}
        for l in ('ui.error', 'control'):
            self._markers[l] = m = self.markerDefine(QsciScintilla.Background)
            c = QColor(qtlib.getbgcoloreffect(l))
            if c.isValid():
                self.setMarkerBackgroundColor(c, m)
            # NOTE: self.setMarkerForegroundColor() doesn't take effect,
            # because it's a *Background* marker.

    @pyqtSlot(unicode, str)
    def appendLog(self, msg, label):
        """Append log text to the last line; scrolls down to there"""
        self.append(msg)
        self._setmarker(xrange(self.lines() - unicode(msg).count('\n') - 1,
                               self.lines() - 1), label)
        self.setCursorPosition(self.lines() - 1, 0)

    def _setmarker(self, lines, label):
        for m in self._markersforlabel(label):
            for i in lines:
                self.markerAdd(i, m)

    def _markersforlabel(self, label):
        return iter(self._markers[l] for l in str(label).split()
                    if l in self._markers)

    @pyqtSlot()
    def clearLog(self):
        """This slot can be overridden by subclass to do more actions"""
        self.clear()

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        menu.addAction(_('Clea&r Log'), self.clearLog)
        menu.exec_(event.globalPos())
        menu.setParent(None)

class Widget(QWidget):
    """An embeddable widget for running Mercurial command"""

    commandStarted = pyqtSignal()
    commandFinished = pyqtSignal(int)
    commandCanceling = pyqtSignal()

    output = pyqtSignal(QString, QString)
    progress = pyqtSignal(QString, object, QString, QString, object)
    makeLogVisible = pyqtSignal(bool)

    def __init__(self, logWindow, statusBar, parent):
        super(Widget, self).__init__(parent)

        self.core = Core(logWindow, self)
        self.core.commandStarted.connect(self.commandStarted)
        self.core.commandFinished.connect(self.onCommandFinished)
        self.core.commandCanceling.connect(self.commandCanceling)
        self.core.output.connect(self.output)
        self.core.progress.connect(self.progress)
        if not logWindow:
            return

        vbox = QVBoxLayout()
        vbox.setSpacing(4)
        vbox.setContentsMargins(*(1,)*4)
        self.setLayout(vbox)

        # command output area
        self.core.outputLog.setHidden(True)
        self.layout().addWidget(self.core.outputLog, 1)

        if statusBar:
            ## status and progress labels
            self.stbar = ThgStatusBar()
            self.stbar.setSizeGripEnabled(False)
            self.core.setStbar(self.stbar)
            self.layout().addWidget(self.stbar)

    ### Public Methods ###

    def run(self, cmdline, *args, **opts):
        self.core.run(cmdline, *args, **opts)

    def cancel(self):
        self.core.cancel()

    def setShowOutput(self, visible):
        if hasattr(self.core, 'outputLog'):
            self.core.outputLog.setShown(visible)

    def outputShown(self):
        if hasattr(self.core, 'outputLog'):
            return self.core.outputLog.isVisible()
        else:
            return False

    ### Signal Handler ###

    @pyqtSlot(int)
    def onCommandFinished(self, ret):
        if ret == -1:
            self.makeLogVisible.emit(True)
            self.setShowOutput(True)
        self.commandFinished.emit(ret)

class CmdSessionDialog(QDialog):
    """Dialog to monitor running Mercurial commands"""

    def __init__(self, parent=None):
        super(CmdSessionDialog, self).__init__(parent)
        self.setWindowFlags(self.windowFlags()
                            & ~Qt.WindowContextHelpButtonHint)

        vbox = QVBoxLayout()
        vbox.setSpacing(4)
        vbox.setContentsMargins(5, 5, 5, 5)

        # command output area
        self._outputLog = LogWidget(self)
        self._outputLog.installEventFilter(qscilib.KeyPressInterceptor(self))
        vbox.addWidget(self._outputLog, 1)

        ## status and progress labels
        self._stbar = ThgStatusBar()
        self._stbar.setSizeGripEnabled(False)
        vbox.addWidget(self._stbar)

        # bottom buttons
        buttons = QDialogButtonBox()
        self._cancelBtn = buttons.addButton(QDialogButtonBox.Cancel)
        self._cancelBtn.clicked.connect(self.abortCommand)

        self._closeBtn = buttons.addButton(QDialogButtonBox.Close)
        self._closeBtn.clicked.connect(self.reject)

        self._detailBtn = buttons.addButton(_('Detail'),
                                            QDialogButtonBox.ResetRole)
        self._detailBtn.setAutoDefault(False)
        self._detailBtn.setCheckable(True)
        self._detailBtn.setChecked(True)
        self._detailBtn.toggled.connect(self.setLogVisible)
        vbox.addWidget(buttons)

        self.setLayout(vbox)
        self.setWindowTitle(_('TortoiseHg Command Dialog'))
        self.resize(540, 420)

        self._session = cmdcore.nullCmdSession()
        self._updateUi()

    def setSession(self, sess):
        """Start watching the given command session"""
        assert self._session.isFinished()
        self._session = sess
        sess.commandFinished.connect(self._updateUi)
        sess.outputReceived.connect(self._outputLog.appendLog)
        sess.progressReceived.connect(self._stbar.progress)
        self._updateUi()

    @pyqtSlot()
    def abortCommand(self):
        self._session.abort()
        self._cancelBtn.setDisabled(True)

    def setLogVisible(self, visible):
        """show/hide command output"""
        self._outputLog.setVisible(visible)
        self._detailBtn.setChecked(visible)

        # workaround to adjust only window height
        self.setMinimumWidth(self.width())
        self.adjustSize()
        self.setMinimumWidth(0)

    def reject(self):
        if not self._session.isFinished():
            ret = QMessageBox.question(self, _('Confirm Exit'),
                        _('Mercurial command is still running.\n'
                          'Are you sure you want to terminate?'),
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.abortCommand()
            # don't close dialog
            return

        # close dialog
        if self._session.exitCode() == 0:
            self.accept()  # means command successfully finished
        else:
            super(CmdSessionDialog, self).reject()

    @pyqtSlot()
    def _updateUi(self):
        updateStatusMessage(self._stbar, self._session)
        self._cancelBtn.setVisible(not self._session.isFinished())
        self._closeBtn.setVisible(self._session.isFinished())
        if self._session.isFinished():
            self._closeBtn.setFocus()


def errorMessageBox(session, parent=None, title=None):
    """Open a message box to report the error of the given session"""
    if not title:
        title = _('Command Error')
    reason = session.errorString()
    text = session.warningString()
    if text:
        text += '\n\n'
    text += _('[Code: %d]') % session.exitCode()
    return qtlib.WarningMsgBox(title, reason, text, parent=parent)
