# pick.py - Pick dialog for TortoiseHg
#
# Copyright 2010 Steve Borho <steve@borho.org>
# Copyright 2020 Matt Harbison <mharbison72@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from __future__ import absolute_import

from mercurial import (
    state as statemod,
)

from .qtcore import (
    QSettings,
    QTimer,
    Qt,
    pyqtSlot,
)
from .qtgui import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QMessageBox,
    QVBoxLayout,
)

from ..util import hglib
from ..util.i18n import _
from . import (
    cmdcore,
    cmdui,
    csinfo,
    qtlib,
    resolve,
    thgrepo,
    wctxcleaner,
)


class PickDialog(QDialog):
    def __init__(self, repoagent, parent, **opts):
        super(PickDialog, self).__init__(parent)

        self.cmdstate = statemod.cmdstate(repoagent.rawRepo(), b"pickstate")
        # TODO: self.setWindowIcon(qtlib.geticon('hg-pick'))
        self.setWindowFlags(self.windowFlags()
                            & ~Qt.WindowContextHelpButtonHint)
        self._repoagent = repoagent
        self._cmdsession = cmdcore.nullCmdSession()
        self.opts = opts

        box = QVBoxLayout()
        box.setSpacing(8)
        box.setContentsMargins(*(6,)*4)
        self.setLayout(box)

        style = csinfo.panelstyle(selectable=True)

        srcb = QGroupBox(_('Pick changeset'))
        srcb.setLayout(QVBoxLayout())
        srcb.layout().setContentsMargins(*(2,)*4)
        source = csinfo.create(self.repo, opts['rev'], style, withupdate=True)
        srcb.layout().addWidget(source)
        self.sourcecsinfo = source
        box.addWidget(srcb)

        sep = qtlib.LabeledSeparator(_('Options'))
        box.addWidget(sep)

        self.autoresolvechk = QCheckBox(_('Automatically resolve merge '
                                          'conflicts where possible'))
        box.addWidget(self.autoresolvechk)

        self._cmdlog = cmdui.LogWidget(self)
        self._cmdlog.hide()
        box.addWidget(self._cmdlog, 2)
        self._stbar = cmdui.ThgStatusBar(self)
        self._stbar.setSizeGripEnabled(False)
        self._stbar.linkActivated.connect(self.linkActivated)
        box.addWidget(self._stbar)

        bbox = QDialogButtonBox()
        self.cancelbtn = bbox.addButton(QDialogButtonBox.Cancel)
        self.cancelbtn.clicked.connect(self.reject)

        self.runbtn = bbox.addButton(_('Pick'),
                                     QDialogButtonBox.ActionRole)
        self.runbtn.clicked.connect(self.runCommand)

        self.abortbtn = bbox.addButton(_('Abort'),
                                       QDialogButtonBox.ActionRole)
        self.abortbtn.clicked.connect(self.abort)
        box.addWidget(bbox)

        self._wctxcleaner = wctxcleaner.WctxCleaner(repoagent, self)
        self._wctxcleaner.checkFinished.connect(self._onWctxCheckFinished)

        if self.checkResolve():
            for w in (srcb, sep):
                w.setHidden(True)
            self._cmdlog.show()
        else:
            self._stbar.showMessage(_('Checking...'))
            self.abortbtn.setEnabled(False)
            self.runbtn.setEnabled(False)
            QTimer.singleShot(0, self._wctxcleaner.check)

        self.setMinimumWidth(480)
        self.setMaximumHeight(800)
        self.resize(0, 340)
        self.setWindowTitle(_('Pick - %s') % repoagent.displayName())
        self._readSettings()

    @property
    def repo(self):
        return self._repoagent.rawRepo()

    def _readSettings(self):
        """Initialize widgets on this dialog from persistent storage.
        """
        qs = QSettings()
        qs.beginGroup('pick')
        self.autoresolvechk.setChecked(
            self._repoagent.configBool('tortoisehg', 'autoresolve',
                                       qtlib.readBool(qs, 'autoresolve', True)))
        qs.endGroup()

    def _writeSettings(self):
        """Save the option widget states on this dialog to persistent storage.
        """
        qs = QSettings()
        qs.beginGroup('pick')
        qs.setValue('autoresolve', self.autoresolvechk.isChecked())
        qs.endGroup()

    @pyqtSlot(bool)
    def _onWctxCheckFinished(self, clean):
        """The callback when the command to check that wdir is clean completes.
        """
        if not clean:
            self.runbtn.setEnabled(False)
            txt = _('Before pick, you must '
                    '<a href="commit"><b>commit</b></a>, '
                    '<a href="shelve"><b>shelve</b></a> to patch, '
                    'or <a href="discard"><b>discard</b></a> changes.')
        else:
            self.runbtn.setEnabled(True)
            txt = _('You may continue the pick')
        self._stbar.showMessage(txt)

    def runCommand(self):
        """The handler for clicking the operation action button.

        This issues the main command for the dialog, or ``--continue`` if there
        is an interrupted operation.
        """
        self.runbtn.setEnabled(False)
        self.cancelbtn.setVisible(False)

        itool = self.autoresolvechk.isChecked() and 'merge' or 'fail'
        opts = {'config': 'ui.merge=internal:%s' % itool}
        if self.cmdstate.exists():
            opts['continue'] = True
        else:
            opts['rev'] = hglib.tounicode(str(self.opts.get('rev')))

        cmdline = hglib.buildcmdargs('pick', **opts)

        sess = self._runCommand(cmdline)
        sess.commandFinished.connect(self._commandFinished)

    def abort(self):
        """The handler for clicking the Abort button.

        This issues a command to abort the interrupted operation.
        """
        cmdline = hglib.buildcmdargs('pick', abort=True)
        sess = self._runCommand(cmdline)
        sess.commandFinished.connect(self._abortFinished)

    def _runCommand(self, cmdline):
        assert self._cmdsession.isFinished()
        self._cmdsession = sess = self._repoagent.runCommand(cmdline, self)
        sess.commandFinished.connect(self._stbar.clearProgress)
        sess.outputReceived.connect(self._cmdlog.appendLog)
        sess.progressReceived.connect(self._stbar.setProgress)
        cmdui.updateStatusMessage(self._stbar, sess)
        return sess

    @pyqtSlot(int)
    def _commandFinished(self, ret):
        """The callback when the main command (or ``--continue``) completes."""
        # TODO since hg 2.6, pick will end with ret=1 in case of "unresolved
        # conflicts", so we can fine-tune checkResolve() later.
        if self.checkResolve() is False:
            msg = _('Pick is complete')
            if ret == 255:
                msg = _('Pick failed')
                self._cmdlog.show()  # contains hint
            self._stbar.showMessage(msg, error=(ret == 255))
            self._makeCloseButton()

    @pyqtSlot()
    def _abortFinished(self):
        """The callback when the abort command completes."""
        if self.checkResolve() is False:
            self._stbar.showMessage(_('Pick aborted'))
            self._makeCloseButton()

    def _makeCloseButton(self):
        self.runbtn.setEnabled(True)
        self.runbtn.setText(_('Close'))
        self.runbtn.clicked.disconnect(self.runCommand)
        self.runbtn.clicked.connect(self.accept)

    def checkResolve(self):
        for root, path, status in thgrepo.recursiveMergeStatus(self.repo):
            if status == b'u':
                txt = _('Pick generated merge <b>conflicts</b> that must '
                        'be <a href="resolve"><b>resolved</b></a>')
                self.runbtn.setEnabled(False)
                break
        else:
            self.runbtn.setEnabled(True)
            txt = _('You may continue the pick')
        self._stbar.showMessage(txt)

        if self.cmdstate.exists():
            self.abortbtn.setEnabled(True)
            self.runbtn.setText('Continue')
            return True
        else:
            self.abortbtn.setEnabled(False)
            return False

    def linkActivated(self, cmd):
        if cmd == 'resolve':
            dlg = resolve.ResolveDialog(self._repoagent, self)
            dlg.exec_()
            self.checkResolve()
        else:
            self._wctxcleaner.runCleaner(cmd)

    def reject(self):
        """The handler for clicking the Cancel button.

        If the user confirms the cancellation, the operation is left in the
        interrupted state.
        """
        if self.cmdstate.exists():
            main = _('Exiting with an unfinished pick is not recommended.')
            text = _('Consider aborting the pick first.')
            labels = ((QMessageBox.Yes, _('&Exit')),
                      (QMessageBox.No, _('Cancel')))
            if not qtlib.QuestionMsgBox(_('Confirm Exit'), main, text,
                                        labels=labels, parent=self):
                return
        super(PickDialog, self).reject()

    def done(self, r):
        self._writeSettings()
        super(PickDialog, self).done(r)
