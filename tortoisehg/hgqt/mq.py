# mq.py - TortoiseHg MQ widget
#
# Copyright 2011 Steve Borho <steve@borho.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import os, re

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from mercurial import error, util

from tortoisehg.util import hglib
from tortoisehg.hgqt.i18n import _
from tortoisehg.hgqt import cmdcore, qtlib, cmdui
from tortoisehg.hgqt import commit, qdelete, qfold, qrename, rejects

def _checkForRejects(repo, rawoutput, parent=None):
    """Parse output of qpush/qpop to resolve hunk failure manually"""
    rejre = re.compile('saving rejects to file (.*).rej')
    rejfiles = [m.group(1) for m in rejre.finditer(rawoutput)
                if os.path.exists(repo.wjoin(m.group(1)))]
    for wfile in rejfiles:
        ufile = hglib.tounicode(wfile)
        if qtlib.QuestionMsgBox(_('Manually resolve rejected chunks?'),
                                _('%s had rejected chunks, edit patched '
                                  'file together with rejects?') % ufile,
                                parent=parent):
            dlg = rejects.RejectsDialog(repo.ui, repo.wjoin(wfile), parent)
            dlg.exec_()

    return len(rejfiles)

class QueueManagementActions(QObject):
    """Container for patch queue management actions"""

    def __init__(self, parent=None):
        super(QueueManagementActions, self).__init__(parent)
        assert parent is None or isinstance(parent, QWidget)
        self._repoagent = None
        self._cmdsession = cmdcore.nullCmdSession()

        self._actions = {
            'commitQueue': QAction(_('&Commit to Queue...'), self),
            'createQueue': QAction(_('Create &New Queue...'), self),
            'renameQueue': QAction(_('&Rename Active Queue...'), self),
            'deleteQueue': QAction(_('&Delete Queue...'), self),
            'purgeQueue':  QAction(_('&Purge Queue...'), self),
            }
        for name, action in self._actions.iteritems():
            action.triggered.connect(getattr(self, '_' + name))
        self._updateActions()

    def setRepoAgent(self, repoagent):
        self._repoagent = repoagent
        self._updateActions()

    def _updateActions(self):
        enabled = bool(self._repoagent) and self._cmdsession.isFinished()
        for action in self._actions.itervalues():
            action.setEnabled(enabled)

    def createMenu(self, parent=None):
        menu = QMenu(parent)
        menu.addAction(self._actions['commitQueue'])
        menu.addSeparator()
        for name in ['createQueue', 'renameQueue', 'deleteQueue', 'purgeQueue']:
            menu.addAction(self._actions[name])
        return menu

    @pyqtSlot()
    def _commitQueue(self):
        assert self._repoagent
        repo = self._repoagent.rawRepo()
        if os.path.isdir(repo.mq.join('.hg')):
            self._launchCommitDialog()
            return
        if not self._cmdsession.isFinished():
            return

        cmdline = hglib.buildcmdargs('init', mq=True)
        self._cmdsession = sess = self._repoagent.runCommand(cmdline, self)
        sess.commandFinished.connect(self._onQueueRepoInitialized)
        self._updateActions()

    @pyqtSlot(int)
    def _onQueueRepoInitialized(self, ret):
        if ret == 0:
            self._launchCommitDialog()
        self._onCommandFinished(ret)

    def _launchCommitDialog(self):
        if not self._repoagent:
            return
        repo = self._repoagent.rawRepo()
        repoagent = self._repoagent.subRepoAgent(hglib.tounicode(repo.mq.path))
        dlg = commit.CommitDialog(repoagent, [], {}, self.parent())
        dlg.finished.connect(dlg.deleteLater)
        dlg.exec_()

    def switchQueue(self, name):
        return self._runQqueue(None, name)

    @pyqtSlot()
    def _createQueue(self):
        name = self._getNewName(_('Create Patch Queue'),
                                _('New patch queue name'),
                                _('Create'))
        if name:
            self._runQqueue('create', name)

    @pyqtSlot()
    def _renameQueue(self):
        curname = self._activeName()
        newname = self._getNewName(_('Rename Patch Queue'),
                                   _("Rename patch queue '%s' to") % curname,
                                   _('Rename'))
        if newname and curname != newname:
            self._runQqueue('rename', newname)

    @pyqtSlot()
    def _deleteQueue(self):
        name = self._getExistingName(_('Delete Patch Queue'),
                                     _('Delete reference to'),
                                     _('Delete'))
        if name:
            self._runQqueueInactive('delete', name)

    @pyqtSlot()
    def _purgeQueue(self):
        name = self._getExistingName(_('Purge Patch Queue'),
                                     _('Remove patch directory of'),
                                     _('Purge'))
        if name:
            self._runQqueueInactive('purge', name)

    def _activeName(self):
        assert self._repoagent
        repo = self._repoagent.rawRepo()
        return hglib.tounicode(repo.thgactivemqname)

    def _existingNames(self):
        assert self._repoagent
        return hglib.getqqueues(self._repoagent.rawRepo())

    def _getNewName(self, title, labeltext, oktext):
        dlg = QInputDialog(self.parent())
        dlg.setWindowTitle(title)
        dlg.setLabelText(labeltext)
        dlg.setOkButtonText(oktext)
        if dlg.exec_():
            return dlg.textValue()

    def _getExistingName(self, title, labeltext, oktext):
        dlg = QInputDialog(self.parent())
        dlg.setWindowTitle(title)
        dlg.setLabelText(labeltext)
        dlg.setOkButtonText(oktext)
        dlg.setComboBoxEditable(False)
        dlg.setComboBoxItems(self._existingNames())
        dlg.setTextValue(self._activeName())
        if dlg.exec_():
            return dlg.textValue()

    def abort(self):
        self._cmdsession.abort()

    def _runQqueue(self, op, name):
        """Execute qqueue operation against the specified queue"""
        assert self._repoagent
        if not self._cmdsession.isFinished():
            return cmdcore.nullCmdSession()

        opts = {}
        if op:
            opts[op] = True
        cmdline = hglib.buildcmdargs('qqueue', name, **opts)
        self._cmdsession = sess = self._repoagent.runCommand(cmdline, self)
        sess.commandFinished.connect(self._onCommandFinished)
        self._updateActions()
        return sess

    def _runQqueueInactive(self, op, name):
        """Execute qqueue operation after inactivating the specified queue"""
        assert self._repoagent
        if not self._cmdsession.isFinished():
            return cmdcore.nullCmdSession()

        if name != self._activeName():
            return self._runQqueue(op, name)

        sacrifices = [n for n in self._existingNames() if n != name]
        if not sacrifices:
            return self._runQqueue(op, name)  # will exit with error

        opts = {}
        if op:
            opts[op] = True
        cmdlines = [hglib.buildcmdargs('qqueue', sacrifices[0]),
                    hglib.buildcmdargs('qqueue', name, **opts)]
        self._cmdsession = sess = self._repoagent.runCommandSequence(cmdlines,
                                                                     self)
        sess.commandFinished.connect(self._onCommandFinished)
        self._updateActions()
        return sess

    @pyqtSlot(int)
    def _onCommandFinished(self, ret):
        if ret != 0:
            cmdui.errorMessageBox(self._cmdsession, self.parent())
        self._updateActions()


class PatchQueueActions(QObject):
    """Container for MQ patch actions except for queue management"""

    def __init__(self, parent=None):
        super(PatchQueueActions, self).__init__(parent)
        assert parent is None or isinstance(parent, QWidget)
        self._repoagent = None
        self._cmdsession = cmdcore.nullCmdSession()
        self._opts = {'force': False, 'keep_changes': False}

    def setRepoAgent(self, repoagent):
        self._repoagent = repoagent

    def gotoPatch(self, patch):
        opts = {'force': self._opts['force'],
                'keep_changes': self._opts['keep_changes']}
        return self._runCommand('qgoto', [patch], opts, self._onPushFinished)

    @pyqtSlot()
    def pushPatch(self, patch=None, move=False, exact=False):
        return self._runPush(patch, move=move, exact=exact)

    @pyqtSlot()
    def pushAllPatches(self):
        return self._runPush(None, all=True)

    def _runPush(self, patch, **opts):
        opts['force'] = self._opts['force']
        if not opts.get('exact'):
            # --exact and --keep-changes cannot be used simultaneously
            # thus we ignore the "default" setting for --keep-changes
            # when --exact is explicitly set
            opts['keep_changes'] = self._opts['keep_changes']
        return self._runCommand('qpush', [patch], opts, self._onPushFinished)

    @pyqtSlot()
    def popPatch(self, patch=None):
        return self._runPop(patch)

    @pyqtSlot()
    def popAllPatches(self):
        return self._runPop(None, all=True)

    def _runPop(self, patch, **opts):
        opts['force'] = self._opts['force']
        opts['keep_changes'] = self._opts['keep_changes']
        return self._runCommand('qpop', [patch], opts)

    def deletePatches(self, patches):
        dlg = qdelete.QDeleteDialog(patches, self.parent())
        if not dlg.exec_():
            return cmdcore.nullCmdSession()
        return self._runCommand('qdelete', patches, dlg.options())

    def foldPatches(self, patches):
        lpatches = map(hglib.fromunicode, patches)
        dlg = qfold.QFoldDialog(self._repoagent, lpatches, self.parent())
        dlg.finished.connect(dlg.deleteLater)
        if not dlg.exec_():
            return cmdcore.nullCmdSession()
        return self._runCommand('qfold', dlg.patches(), dlg.options())

    def renamePatch(self, patch):
        newname = patch
        while True:
            newname = self._getNewName(_('Rename Patch'),
                                       _('Rename patch <b>%s</b> to:') % patch,
                                       newname, _('Rename'))
            if not newname or patch == newname:
                return cmdcore.nullCmdSession()
            repo = self._repoagent.rawRepo()
            newfilename = hglib.tounicode(
                repo.mq.join(hglib.fromunicode(newname)))
            ok = qrename.checkPatchname(newfilename, self.parent())
            if ok:
                break
        return self._runCommand('qrename', [patch, newname], {})

    def guardPatch(self, patch, guards):
        args = [patch]
        args.extend(guards)
        opts = {'none': not guards}
        return self._runCommand('qguard', args, opts)

    def selectGuards(self, guards):
        opts = {'none': not guards}
        return self._runCommand('qselect', guards, opts)

    def _getNewName(self, title, labeltext, curvalue, oktext):
        dlg = QInputDialog(self.parent())
        dlg.setWindowTitle(title)
        dlg.setLabelText(labeltext)
        dlg.setTextValue(curvalue)
        dlg.setOkButtonText(oktext)
        if dlg.exec_():
            return unicode(dlg.textValue())

    def abort(self):
        self._cmdsession.abort()

    def _runCommand(self, name, args, opts, finishslot=None):
        assert self._repoagent
        if not self._cmdsession.isFinished():
            return cmdcore.nullCmdSession()
        cmdline = hglib.buildcmdargs(name, *args, **opts)
        self._cmdsession = sess = self._repoagent.runCommand(cmdline, self)
        sess.commandFinished.connect(finishslot or self._onCommandFinished)
        return sess

    @pyqtSlot(int)
    def _onPushFinished(self, ret):
        if ret == 2 and self._repoagent:
            repo = self._repoagent.rawRepo()
            output = hglib.fromunicode(self._cmdsession.warningString())
            if _checkForRejects(repo, output, self.parent()) > 0:
                ret = 0  # no further error dialog
        if ret != 0:
            cmdui.errorMessageBox(self._cmdsession, self.parent())

    @pyqtSlot(int)
    def _onCommandFinished(self, ret):
        if ret != 0:
            cmdui.errorMessageBox(self._cmdsession, self.parent())

    @pyqtSlot()
    def launchOptionsDialog(self):
        dlg = OptionsDialog(self._opts, self.parent())
        dlg.finished.connect(dlg.deleteLater)
        dlg.setWindowFlags(Qt.Sheet)
        dlg.setWindowModality(Qt.WindowModal)
        if dlg.exec_() == QDialog.Accepted:
            self._opts.update(dlg.outopts)


class PatchQueueModel(QAbstractListModel):
    """List of all patches in active queue"""

    def __init__(self, repoagent, parent=None):
        super(PatchQueueModel, self).__init__(parent)
        self._repoagent = repoagent
        self._repoagent.repositoryChanged.connect(self._updateCache)
        self._series = []
        self._seriesguards = []
        self._statusmap = {}  # patch: applied/guarded/unguarded
        self._buildCache()

    @pyqtSlot()
    def _updateCache(self):
        # optimize range of changed signals if necessary
        repo = self._repoagent.rawRepo()
        if self._series == repo.mq.series[::-1]:
            self._buildCache()
        else:
            self._updateCacheAndLayout()
        self.dataChanged.emit(self.index(0), self.index(self.rowCount() - 1))

    def _updateCacheAndLayout(self):
        self.layoutAboutToBeChanged.emit()
        oldindexes = [(oi, self._series[oi.row()])
                      for oi in self.persistentIndexList()]
        self._buildCache()
        for oi, patch in oldindexes:
            try:
                ni = self.index(self._series.index(patch), oi.column())
            except ValueError:
                ni = QModelIndex()
            self.changePersistentIndex(oi, ni)
        self.layoutChanged.emit()

    def _buildCache(self):
        repo = self._repoagent.rawRepo()
        self._series = repo.mq.series[::-1]
        self._seriesguards = [list(xs) for xs in reversed(repo.mq.seriesguards)]

        self._statusmap.clear()
        self._statusmap.update((p.name, 'applied') for p in repo.mq.applied)
        for i, patch in enumerate(repo.mq.series):
            if patch in self._statusmap:
                continue  # applied
            pushable, why = repo.mq.pushable(i)
            if not pushable:
                self._statusmap[patch] = 'guarded'
            elif why is not None:
                self._statusmap[patch] = 'unguarded'

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.patchName(index)
        if role == Qt.DecorationRole:
            return self._statusIcon(index)
        if role == Qt.FontRole:
            return self._statusFont(index)
        if role == Qt.ToolTipRole:
            return self._toolTip(index)

    def flags(self, index):
        flags = super(PatchQueueModel, self).flags(index)
        if not index.isValid():
            return flags | Qt.ItemIsDropEnabled  # insertion point
        patch = self._series[index.row()]
        if self._statusmap.get(patch) != 'applied':
            flags |= Qt.ItemIsDragEnabled
        return flags

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._series)

    def appliedCount(self):
        return sum(s == 'applied' for s in self._statusmap.itervalues())

    def patchName(self, index):
        if not index.isValid():
            return ''
        return hglib.tounicode(self._series[index.row()])

    def patchGuards(self, index):
        if not index.isValid():
            return []
        return map(hglib.tounicode, self._seriesguards[index.row()])

    def isApplied(self, index):
        if not index.isValid():
            return False
        patch = self._series[index.row()]
        return self._statusmap.get(patch) == 'applied'

    def _statusIcon(self, index):
        assert index.isValid()
        patch = self._series[index.row()]
        status = self._statusmap.get(patch)
        if status:
            return qtlib.geticon('hg-patch-%s' % status)

    def _statusFont(self, index):
        assert index.isValid()
        patch = self._series[index.row()]
        status = self._statusmap.get(patch)
        if status not in ('applied', 'guarded'):
            return
        f = QFont()
        f.setBold(status == 'applied')
        f.setItalic(status == 'guarded')
        return f

    def _toolTip(self, index):
        assert index.isValid()
        repo = self._repoagent.rawRepo()
        patch = self._series[index.row()]
        try:
            ctx = repo.changectx(patch)
        except error.RepoLookupError:
            # cache not updated after qdelete or qfinish
            return
        guards = self.patchGuards(index)
        return '%s: %s\n%s' % (self.patchName(index),
                               guards and ', '.join(guards) or _('no guards'),
                               ctx.longsummary())

    def mimeTypes(self):
        return ['application/vnd.thg.mq.series', 'text/uri-list']

    def mimeData(self, indexes):
        repo = self._repoagent.rawRepo()
        # in the same order as series file
        patches = [self._series[i.row()]
                   for i in sorted(indexes, reverse=True)]
        data = QMimeData()
        data.setData('application/vnd.thg.mq.series',
                     QByteArray('\n'.join(patches) + '\n'))
        data.setUrls([QUrl.fromLocalFile(hglib.tounicode(repo.mq.join(p)))
                      for p in patches])
        return data

    def dropMimeData(self, data, action, row, column, parent):
        if (action != Qt.MoveAction
            or not data.hasFormat('application/vnd.thg.mq.series')
            or row < 0 or parent.isValid()):
            return False

        repo = self._repoagent.rawRepo()
        qtiprow = len(self._series) - repo.mq.seriesend(True)
        if row > qtiprow:
            return False
        if row < len(self._series):
            after = self._series[row]
        else:
            after = None  # next to working rev
        patches = str(data.data('application/vnd.thg.mq.series')).splitlines()
        if hglib.movemqpatches(repo, after, patches):
            self._repoagent.pollStatus()
        return True

    def supportedDropActions(self):
        return Qt.MoveAction


class MQPatchesWidget(QDockWidget):
    patchSelected = pyqtSignal(unicode)

    def __init__(self, parent):
        QDockWidget.__init__(self, parent)
        self._repoagent = None

        self.setFeatures(QDockWidget.DockWidgetClosable |
                         QDockWidget.DockWidgetMovable  |
                         QDockWidget.DockWidgetFloatable)
        self.setWindowTitle(_('Patch Queue'))

        w = QWidget()
        mainlayout = QVBoxLayout()
        mainlayout.setContentsMargins(0, 0, 0, 0)
        w.setLayout(mainlayout)
        self.setWidget(w)

        self.patchActions = PatchQueueActions(self)

        # top toolbar
        w = QWidget()
        tbarhbox = QHBoxLayout()
        tbarhbox.setContentsMargins(0, 0, 0, 0)
        w.setLayout(tbarhbox)
        mainlayout.addWidget(w)

        # TODO: move QAction instances to PatchQueueActions
        self.qpushAllAct = a = QAction(
            qtlib.geticon('hg-qpush-all'), _('Push all', 'MQ QPush'), self)
        a.setToolTip(_('Apply all patches'))
        self.qpushAct = a = QAction(
            qtlib.geticon('hg-qpush'), _('Push', 'MQ QPush'), self)
        a.setToolTip(_('Apply one patch'))
        self.setGuardsAct = a = QAction(
            qtlib.geticon('hg-qguard'), _('Set &Guards...'), self)
        a.setToolTip(_('Configure guards for selected patch'))
        self.qdeleteAct = a = QAction(
            qtlib.geticon('hg-qdelete'), _('&Delete Patches...'), self)
        a.setToolTip(_('Delete selected patches'))
        self.qpopAct = a = QAction(
            qtlib.geticon('hg-qpop'), _('Pop'), self)
        a.setToolTip(_('Unapply one patch'))
        self.qpopAllAct = a = QAction(
            qtlib.geticon('hg-qpop-all'), _('Pop all'), self)
        a.setToolTip(_('Unapply all patches'))
        self.qrenameAct = QAction(_('Re&name Patch...'), self)
        self.qtbar = tbar = QToolBar(_('Patch Queue Actions Toolbar'))
        tbar.setIconSize(qtlib.smallIconSize())
        tbarhbox.addWidget(tbar)
        tbar.addAction(self.qpushAct)
        tbar.addAction(self.qpushAllAct)
        tbar.addSeparator()
        tbar.addAction(self.qpopAct)
        tbar.addAction(self.qpopAllAct)
        tbar.addSeparator()
        tbar.addAction(self.qdeleteAct)
        tbar.addSeparator()
        tbar.addAction(self.setGuardsAct)

        self.queueFrame = w = QFrame()
        mainlayout.addWidget(w)

        # Patch Queue Frame
        layout = QVBoxLayout()
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)
        self.queueFrame.setLayout(layout)

        qqueuehbox = QHBoxLayout()
        qqueuehbox.setSpacing(5)
        layout.addLayout(qqueuehbox)
        self.qqueueComboWidget = QComboBox(self)
        qqueuehbox.addWidget(self.qqueueComboWidget, 1)
        self.qqueueConfigBtn = QToolButton(self)
        self.qqueueConfigBtn.setText('...')
        self.qqueueConfigBtn.setPopupMode(QToolButton.InstantPopup)
        qqueuehbox.addWidget(self.qqueueConfigBtn)

        self.qqueueActions = QueueManagementActions(self)
        self.qqueueConfigBtn.setMenu(self.qqueueActions.createMenu(self))

        self.queueListWidget = QListView(self)
        self.queueListWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.queueListWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.queueListWidget.setIconSize(qtlib.smallIconSize() * 0.75)
        self.queueListWidget.setSelectionMode(
            QAbstractItemView.ExtendedSelection)
        self.queueListWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.queueListWidget.customContextMenuRequested.connect(
            self.onMenuRequested)
        layout.addWidget(self.queueListWidget, 1)

        bbarhbox = QHBoxLayout()
        bbarhbox.setSpacing(5)
        layout.addLayout(bbarhbox)
        self.guardSelBtn = QPushButton()
        menu = QMenu(self)
        menu.triggered.connect(self.onGuardSelectionChange)
        self.guardSelBtn.setMenu(menu)
        bbarhbox.addWidget(self.guardSelBtn)

        self.qqueueComboWidget.activated[QString].connect(
            self.onQQueueActivated)

        self.queueListWidget.activated.connect(self.onGotoPatch)

        self.qpushAllAct.triggered.connect(self.patchActions.pushAllPatches)
        self.qpushAct.triggered[()].connect(self.patchActions.pushPatch)
        self.qpopAllAct.triggered.connect(self.patchActions.popAllPatches)
        self.qpopAct.triggered[()].connect(self.patchActions.popPatch)
        self.setGuardsAct.triggered.connect(self.onGuardConfigure)
        self.qdeleteAct.triggered.connect(self.onDelete)
        self.qrenameAct.triggered.connect(self.onRenamePatch)

        self.setAcceptDrops(True)

        self.layout().setContentsMargins(2, 2, 2, 2)

        QTimer.singleShot(0, self.reload)

    @property
    def repo(self):
        if self._repoagent:
            return self._repoagent.rawRepo()

    def setRepoAgent(self, repoagent):
        if self._repoagent:
            self._repoagent.repositoryChanged.disconnect(self.reload)
        self._repoagent = None
        if repoagent and 'mq' in repoagent.rawRepo().extensions():
            self._repoagent = repoagent
            self._repoagent.repositoryChanged.connect(self.reload)
        self._changePatchQueueModel()
        self.patchActions.setRepoAgent(repoagent)
        self.qqueueActions.setRepoAgent(repoagent)
        QTimer.singleShot(0, self.reload)

    def _changePatchQueueModel(self):
        oldmodel = self.queueListWidget.model()
        if self._repoagent:
            newmodel = PatchQueueModel(self._repoagent, self)
            self.queueListWidget.setModel(newmodel)
            newmodel.dataChanged.connect(self._updatePatchActions)
            selmodel = self.queueListWidget.selectionModel()
            selmodel.currentRowChanged.connect(self.onPatchSelected)
            selmodel.selectionChanged.connect(self._updatePatchActions)
            self._updatePatchActions()
        else:
            self.queueListWidget.setModel(None)
        if oldmodel:
            oldmodel.setParent(None)

    @pyqtSlot()
    def showActiveQueue(self):
        combo = self.qqueueComboWidget
        q = hglib.tounicode(self.repo.thgactivemqname)
        index = combo.findText(q)
        combo.setCurrentIndex(index)

    @pyqtSlot(QPoint)
    def onMenuRequested(self, pos):
        menu = QMenu(self)
        menu.addAction(self.qdeleteAct)
        menu.addAction(self.qrenameAct)
        menu.addAction(self.setGuardsAct)
        menu.exec_(self.queueListWidget.viewport().mapToGlobal(pos))
        menu.setParent(None)

    @pyqtSlot()
    def onGuardConfigure(self):
        model = self.queueListWidget.model()
        index = self.queueListWidget.currentIndex()
        patch = model.patchName(index)
        uguards = ' '.join(model.patchGuards(index))
        new, ok = qtlib.getTextInput(self,
                      _('Configure guards'),
                      _('Input new guards for %s:') % patch,
                      text=uguards)
        if not ok or new == uguards:
            return
        self.patchActions.guardPatch(patch, unicode(new).split())

    @pyqtSlot()
    def onDelete(self):
        model = self.queueListWidget.model()
        selmodel = self.queueListWidget.selectionModel()
        patches = map(model.patchName, selmodel.selectedRows())
        self.patchActions.deletePatches(patches)

    #@pyqtSlot(QModelIndex)
    def onGotoPatch(self, index):
        'Patch has been activated (return), issue qgoto'
        patch = self.queueListWidget.model().patchName(index)
        self.patchActions.gotoPatch(patch)

    @pyqtSlot()
    def onRenamePatch(self):
        index = self.queueListWidget.currentIndex()
        patch = self.queueListWidget.model().patchName(index)
        self.patchActions.renamePatch(patch)

    #@pyqtSlot(QModelIndex)
    def onPatchSelected(self, index):
        if index.isValid():
            model = self.queueListWidget.model()
            self.patchSelected.emit(model.patchName(index))

    @pyqtSlot()
    def _updatePatchActions(self):
        model = self.queueListWidget.model()
        selmodel = self.queueListWidget.selectionModel()

        appliedcnt = model.appliedCount()
        seriescnt = model.rowCount()
        self.qpushAllAct.setEnabled(seriescnt > appliedcnt)
        self.qpushAct.setEnabled(seriescnt > appliedcnt)
        self.qpopAct.setEnabled(appliedcnt > 0)
        self.qpopAllAct.setEnabled(appliedcnt > 0)

        indexes = selmodel.selectedRows()
        anyapplied = util.any(model.isApplied(i) for i in indexes)
        self.qdeleteAct.setEnabled(len(indexes) > 0 and not anyapplied)
        self.setGuardsAct.setEnabled(len(indexes) == 1)
        self.qrenameAct.setEnabled(len(indexes) == 1)

    @pyqtSlot(QString)
    def onQQueueActivated(self, text):
        if text == hglib.tounicode(self.repo.thgactivemqname):
            return

        if qtlib.QuestionMsgBox(_('Confirm patch queue switch'),
                _("Do you really want to activate patch queue '%s' ?") % text,
                parent=self, defaultbutton=QMessageBox.No):
            sess = self.qqueueActions.switchQueue(text)
            sess.commandFinished.connect(self.showActiveQueue)
        else:
            self.showActiveQueue()

    @pyqtSlot()
    def reload(self):
        self.widget().setEnabled(bool(self._repoagent))
        if not self._repoagent:
            return

        self.loadQQueues()
        self.showActiveQueue()

        repo = self.repo

        self.allguards = set()
        for idx, patch in enumerate(repo.mq.series):
            patchguards = repo.mq.seriesguards[idx]
            if patchguards:
                for guard in patchguards:
                    self.allguards.add(guard[1:])

        for guard in repo.mq.active():
            self.allguards.add(guard)
        self.refreshSelectedGuards()

        self.qqueueComboWidget.setEnabled(self.qqueueComboWidget.count() > 1)

    def loadQQueues(self):
        repo = self.repo
        combo = self.qqueueComboWidget
        combo.clear()
        combo.addItems(hglib.getqqueues(repo))

    def refreshSelectedGuards(self):
        total = len(self.allguards)
        count = len(self.repo.mq.active())
        menu = self.guardSelBtn.menu()
        menu.clear()
        for guard in self.allguards:
            a = menu.addAction(hglib.tounicode(guard))
            a.setCheckable(True)
            a.setChecked(guard in self.repo.mq.active())
        self.guardSelBtn.setText(_('Guards: %d/%d') % (count, total))
        self.guardSelBtn.setEnabled(bool(total))

    @pyqtSlot(QAction)
    def onGuardSelectionChange(self, action):
        guard = hglib.fromunicode(action.text())
        newguards = self.repo.mq.active()[:]
        if action.isChecked():
            newguards.append(guard)
        elif guard in newguards:
            newguards.remove(guard)
        self.patchActions.selectGuards(map(hglib.tounicode, newguards))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.patchActions.abort()
            self.qqueueActions.abort()
        else:
            return super(MQPatchesWidget, self).keyPressEvent(event)


class OptionsDialog(QDialog):
    'Utility dialog for configuring uncommon options'
    def __init__(self, opts, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(_('MQ options'))

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.forcecb = QCheckBox(
            _('Force push or pop (--force)'))
        layout.addWidget(self.forcecb)

        self.keepcb = QCheckBox(
            _('Tolerate non-conflicting local changes (--keep-changes)'))
        layout.addWidget(self.keepcb)

        self.forcecb.setChecked(opts.get('force', False))
        self.keepcb.setChecked(opts.get('keep_changes', False))

        for cb in [self.forcecb, self.keepcb]:
            cb.clicked.connect(self._resolveopts)

        BB = QDialogButtonBox
        bb = QDialogButtonBox(BB.Ok|BB.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        self.bb = bb
        layout.addWidget(bb)

    @qtlib.senderSafeSlot()
    def _resolveopts(self):
        # cannot use both --force and --keep-changes
        exclmap = {self.forcecb: [self.keepcb],
                   self.keepcb: [self.forcecb],
                   }
        sendercb = self.sender()
        if sendercb.isChecked():
            for cb in exclmap[sendercb]:
                cb.setChecked(False)

    def accept(self):
        outopts = {}
        outopts['force'] = self.forcecb.isChecked()
        outopts['keep_changes'] = self.keepcb.isChecked()
        self.outopts = outopts
        QDialog.accept(self)
