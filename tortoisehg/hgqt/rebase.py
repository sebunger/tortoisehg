# rebase.py - Rebase dialog for TortoiseHg
#
# Copyright 2010 Steve Borho <steve@borho.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import os

from tortoisehg.util import hglib
from tortoisehg.hgqt.i18n import _
from tortoisehg.hgqt import qtlib, csinfo, cmdui, resolve, thgrepo, wctxcleaner

BB = QDialogButtonBox

class RebaseDialog(QDialog):
    showMessage = pyqtSignal(QString)

    def __init__(self, repoagent, parent, **opts):
        super(RebaseDialog, self).__init__(parent)
        self.setWindowIcon(qtlib.geticon('hg-rebase'))
        self.setWindowFlags(self.windowFlags()
                            & ~Qt.WindowContextHelpButtonHint)
        self._repoagent = repoagent
        repo = repoagent.rawRepo()
        self.opts = opts
        self.aborted = False

        box = QVBoxLayout()
        box.setSpacing(8)
        box.setContentsMargins(*(6,)*4)
        self.setLayout(box)

        style = csinfo.panelstyle(selectable=True)

        srcb = QGroupBox( _('Rebase changeset and descendants'))
        srcb.setLayout(QVBoxLayout())
        srcb.layout().setContentsMargins(*(2,)*4)
        s = opts.get('source', '.')
        source = csinfo.create(self.repo, s, style, withupdate=True)
        srcb.layout().addWidget(source)
        self.sourcecsinfo = source
        self.layout().addWidget(srcb)

        destb = QGroupBox( _('To rebase destination'))
        destb.setLayout(QVBoxLayout())
        destb.layout().setContentsMargins(*(2,)*4)
        d = opts.get('dest', '.')
        dest = csinfo.create(self.repo, d, style, withupdate=True)
        destb.layout().addWidget(dest)
        self.destcsinfo = dest
        self.layout().addWidget(destb)

        swaplabel = QLabel('<a href="X">%s</a>'  # don't care href
                           % _('Swap source and destination'))
        swaplabel.linkActivated.connect(self.swap)
        self.layout().addWidget(swaplabel)

        sep = qtlib.LabeledSeparator(_('Options'))
        self.layout().addWidget(sep)

        self.keepchk = QCheckBox(_('Keep original changesets'))
        self.keepchk.setChecked(opts.get('keep', False))
        self.layout().addWidget(self.keepchk)

        self.keepbrancheschk = QCheckBox(_('Keep original branch names'))
        self.keepbrancheschk.setChecked(opts.get('keepbranches', False))
        self.layout().addWidget(self.keepbrancheschk)

        self.collapsechk = QCheckBox(_('Collapse the rebased changesets '))
        self.collapsechk.setChecked(opts.get('collapse', False))
        self.layout().addWidget(self.collapsechk)

        self.basechk = QCheckBox(_('Rebase entire source branch'))
        self.layout().addWidget(self.basechk)

        self.autoresolvechk = QCheckBox(_('Automatically resolve merge '
                                          'conflicts where possible'))
        self.autoresolvechk.setChecked(
            repo.ui.configbool('tortoisehg', 'autoresolve', False))
        self.layout().addWidget(self.autoresolvechk)

        if 'hgsubversion' in repo.extensions():
            self.svnchk = QCheckBox(_('Rebase unpublished onto Subversion head '
                                      '(override source, destination)'))
            self.layout().addWidget(self.svnchk)
        else:
            self.svnchk = None

        self.cmd = cmdui.Widget(True, True, self)
        self.cmd.commandFinished.connect(self.commandFinished)
        self.showMessage.connect(self.cmd.stbar.showMessage)
        self.cmd.stbar.linkActivated.connect(self.linkActivated)
        self.layout().addWidget(self.cmd, 2)

        bbox = QDialogButtonBox()
        self.cancelbtn = bbox.addButton(QDialogButtonBox.Cancel)
        self.cancelbtn.clicked.connect(self.reject)
        self.rebasebtn = bbox.addButton(_('Rebase'),
                                        QDialogButtonBox.ActionRole)
        self.rebasebtn.clicked.connect(self.rebase)
        self.abortbtn = bbox.addButton(_('Abort'),
                                       QDialogButtonBox.ActionRole)
        self.abortbtn.clicked.connect(self.abort)
        self.layout().addWidget(bbox)
        self.bbox = bbox

        self._wctxcleaner = wctxcleaner.WctxCleaner(repoagent, self)
        self._wctxcleaner.checkFinished.connect(self._onCheckFinished)
        if self.checkResolve() or not (s or d):
            for w in (srcb, destb, sep, self.keepchk,
                      self.collapsechk, self.keepbrancheschk):
                w.setHidden(True)
            self.cmd.setShowOutput(True)
        else:
            self.showMessage.emit(_('Checking...'))
            self.abortbtn.setEnabled(False)
            self.rebasebtn.setEnabled(False)
            QTimer.singleShot(0, self._wctxcleaner.check)

        self.setMinimumWidth(480)
        self.setMaximumHeight(800)
        self.resize(0, 340)
        self.setWindowTitle(_('Rebase - %s') % self.repo.displayname)

    @property
    def repo(self):
        return self._repoagent.rawRepo()

    @pyqtSlot(bool)
    def _onCheckFinished(self, clean):
        if not clean:
            self.rebasebtn.setEnabled(False)
            txt = _('Before rebase, you must <a href="commit">'
                    '<b>commit</b></a> or <a href="discard">'
                    '<b>discard</b></a> changes.')
        else:
            self.rebasebtn.setEnabled(True)
            txt = _('You may continue the rebase')
        self.showMessage.emit(txt)

    def rebase(self):
        self.rebasebtn.setEnabled(False)
        self.cancelbtn.setShown(False)
        self.keepchk.setEnabled(False)
        self.keepbrancheschk.setEnabled(False)
        self.basechk.setEnabled(False)
        self.collapsechk.setEnabled(False)
        cmdline = ['rebase', '--repository', self.repo.root]
        cmdline += ['--config', 'ui.merge=internal:' +
                    (self.autoresolvechk.isChecked() and 'merge' or 'fail')]
        if os.path.exists(self.repo.join('rebasestate')):
            cmdline += ['--continue']
        else:
            if self.keepchk.isChecked():
                cmdline += ['--keep']
            if self.keepbrancheschk.isChecked():
                cmdline += ['--keepbranches']
            if self.collapsechk.isChecked():
                cmdline += ['--collapse']
            if self.svnchk is not None and self.svnchk.isChecked():
                cmdline += ['--svn']
            else:
                source = self.opts.get('source')
                dest = self.opts.get('dest')
                sourcearg = '--source'
                if self.basechk.isChecked():
                    sourcearg = '--base'
                cmdline += [sourcearg, str(source), '--dest', str(dest)]
        self.repo.incrementBusyCount()
        self.cmd.run(cmdline)

    def swap(self):
        oldsource = self.opts.get('source', '.')
        olddest = self.opts.get('dest', '.')

        self.sourcecsinfo.update(target=olddest)
        self.destcsinfo.update(target=oldsource)

        self.opts['source'] = olddest
        self.opts['dest'] = oldsource

    def abort(self):
        cmdline = ['rebase', '--repository', self.repo.root, '--abort']
        self.repo.incrementBusyCount()
        self.aborted = True
        self.cmd.run(cmdline)

    def commandFinished(self, ret):
        self.repo.decrementBusyCount()
        # TODO since hg 2.6, rebase will end with ret=1 in case of "unresolved
        # conflicts", so we can fine-tune checkResolve() later.
        if self.checkResolve() is False:
            msg = _('Rebase is complete')
            if self.aborted:
                msg = _('Rebase aborted')
            elif ret == 255:
                msg = _('Rebase failed')
                self.cmd.setShowOutput(True)  # contains hint
            self.showMessage.emit(msg)
            self.rebasebtn.setEnabled(True)
            self.rebasebtn.setText(_('Close'))
            self.rebasebtn.clicked.disconnect(self.rebase)
            self.rebasebtn.clicked.connect(self.accept)

    def checkResolve(self):
        for root, path, status in thgrepo.recursiveMergeStatus(self.repo):
            if status == 'u':
                txt = _('Rebase generated merge <b>conflicts</b> that must '
                        'be <a href="resolve"><b>resolved</b></a>')
                self.rebasebtn.setEnabled(False)
                break
        else:
            self.rebasebtn.setEnabled(True)
            txt = _('You may continue the rebase')
        self.showMessage.emit(txt)

        if os.path.exists(self.repo.join('rebasestate')):
            self.abortbtn.setEnabled(True)
            self.rebasebtn.setText('Continue')
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
        if os.path.exists(self.repo.join('rebasestate')):
            main = _('Exiting with an unfinished rebase is not recommended.')
            text = _('Consider aborting the rebase first.')
            labels = ((QMessageBox.Yes, _('&Exit')),
                      (QMessageBox.No, _('Cancel')))
            if not qtlib.QuestionMsgBox(_('Confirm Exit'), main, text,
                                        labels=labels, parent=self):
                return
        super(RebaseDialog, self).reject()
