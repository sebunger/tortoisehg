# filectxactions.py - context menu actions for repository files
#
# Copyright 2010 Adrian Buehlmann <adrian@cadifra.com>
# Copyright 2010 Steve Borho <steve@borho.org>
# Copyright 2012 Yuya Nishihara <yuya@tcha.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from tortoisehg.hgqt import cmdcore, cmdui, qtlib, revert, visdiff
from tortoisehg.hgqt import filedata
from tortoisehg.hgqt.i18n import _
from tortoisehg.util import hglib

def _lcanonpaths(fds):
    return [hglib.fromunicode(e.canonicalFilePath()) for e in fds]

def _uniqrevs(fds):
    revs = []
    for e in fds:
        if e.rev() >= 0 and not e.rev() in revs:
            revs.append(e.rev())
    return revs

def _tablebuilder(table):
    def slot(text, icon, shortcut, statustip):
        def decorate(func):
            name = func.__name__
            table[name] = (text, icon, shortcut, statustip)
            return pyqtSlot()(func)
        return decorate
    return slot


class FilectxActions(QObject):
    """Container for repository file actions"""

    linkActivated = pyqtSignal(unicode)
    filterRequested = pyqtSignal(QString)
    """Ask the repowidget to change its revset filter"""

    _actiontable = {}
    actionSlot = _tablebuilder(_actiontable)

    def __init__(self, repoagent, parent):
        super(FilectxActions, self).__init__(parent)
        if not isinstance(parent, QWidget):
            raise ValueError('parent must be a QWidget')

        self._repoagent = repoagent
        self._cmdsession = cmdcore.nullCmdSession()
        repo = repoagent.rawRepo()
        self._curfd = filedata.createNullData(repo)
        self._selfds = []

        self._nav_dialogs = qtlib.DialogKeeper(FilectxActions._createnavdialog,
                                               FilectxActions._gennavdialogkey,
                                               self)

        self._actions = {}
        for name, (desc, icon, key, tip) in self._actiontable.iteritems():
            # QAction must be owned by QWidget; otherwise statusTip for context
            # menu cannot be displayed (QTBUG-16114)
            act = QAction(desc, self.parent())
            if icon:
                act.setIcon(qtlib.geticon(icon))
            if key:
                act.setShortcut(key)
            if tip:
                act.setStatusTip(tip)
            QObject.connect(act, SIGNAL('triggered()'),
                            self, SLOT('%s()' % name))
            self._actions[name] = act

        self._updateActions()

    @property
    def _ui(self):
        repo = self._repoagent.rawRepo()
        return repo.ui

    def _fdRepoAgent(self):
        rpath = self._curfd.repoRootPath()
        if not rpath:
            return self._repoagent
        return self._repoagent.subRepoAgent(rpath)

    def _updateActions(self):
        for a in self._actions.itervalues():
            a.setEnabled(self._cmdsession.isFinished())
        if not self._cmdsession.isFinished():
            return

        nosub = not self._curfd.repoRootPath() and not self._curfd.subrepoType()
        real = self._curfd.rev() is not None and self._curfd.rev() >= 0
        wd = self._curfd.rev() is None
        selrevs = _uniqrevs(self._selfds)
        singledir = len(self._selfds) == 1 and self._curfd.isDir()
        singlefile = len(self._selfds) == 1 and not self._curfd.isDir()
        singlehg = len(self._selfds) == 1 and self._curfd.subrepoType() == 'hg'
        for act in ['filterFile']:
            self._actions[act].setEnabled(nosub)
        for act in ['visualDiffToLocal', 'visualDiffFileToLocal', 'editFile',
                    'saveFile']:
            self._actions[act].setEnabled(real)
        for act in ['visualDiff', 'visualDiffFile', 'revertFile']:
            self._actions[act].setEnabled(real or wd)
        for act in ['visualDiffRevs', 'visualDiffFileRevs']:
            self._actions[act].setEnabled(len(selrevs) == 2)
        for act in ['navigateFileLog', 'navigateFileDiff']:
            self._actions[act].setEnabled((real or wd) and singlefile)
        for act in ['openSubrepo']:
            self._actions[act].setEnabled(singlehg)
        for act in ['explore', 'terminal']:
            self._actions[act].setEnabled(singledir)

    def setFileData(self, curfd, selfds=None):
        self._curfd = curfd
        if selfds:
            self._selfds = list(selfds)
        elif not curfd.isNull():
            self._selfds = [curfd]
        else:
            self._selfds = []
        self._updateActions()

    def actions(self):
        """List of the actions; The owner widget should register them"""
        return self._actions.values()

    def action(self, name):
        return self._actions[name]

    def _runCommandSequence(self, cmdlines):
        if not self._cmdsession.isFinished():
            return
        sess = self._repoagent.runCommandSequence(cmdlines, self)
        self._cmdsession = sess
        sess.commandFinished.connect(self._onCommandFinished)
        self._updateActions()

    @pyqtSlot(int)
    def _onCommandFinished(self, ret):
        if ret == 255:
            cmdui.errorMessageBox(self._cmdsession, self.parent())
        self._updateActions()

    @actionSlot(_('File &History'), 'hg-log', 'Shift+Return',
                _('Show the history of the selected file'))
    def navigateFileLog(self):
        from tortoisehg.hgqt import filedialogs
        self._navigate(filedialogs.FileLogDialog)

    @actionSlot(_('Co&mpare File Revisions'), 'compare-files', None,
                _('Compare revisions of the selected file'))
    def navigateFileDiff(self):
        from tortoisehg.hgqt import filedialogs
        self._navigate(filedialogs.FileDiffDialog)

    def _navigate(self, dlgclass):
        repoagent = self._fdRepoAgent()
        repo = repoagent.rawRepo()
        filename = hglib.fromunicode(self._curfd.canonicalFilePath())
        if len(repo.file(filename)) > 0:
            dlg = self._nav_dialogs.open(dlgclass, repoagent, filename)
            dlg.goto(self._curfd.rev())

    def _createnavdialog(self, dlgclass, repoagent, filename):
        return dlgclass(repoagent, filename)

    def _gennavdialogkey(self, dlgclass, repoagent, filename):
        repo = repoagent.rawRepo()
        return dlgclass, repo.wjoin(filename)

    @actionSlot(_('Filter Histor&y'), 'hg-log', None,
                _('Query about changesets affecting the selected files'))
    def filterFile(self):
        if self._curfd.isNull():
            return
        pats = ["file('path:%s')" % fd.filePath() for fd in self._selfds]
        self.filterRequested.emit(' or '.join(pats))

    @actionSlot(_('Diff &Changeset to Parent'), 'visualdiff', None, '')
    def visualDiff(self):
        self._visualDiff([], change=self._curfd.rev())

    @actionSlot(_('Diff Changeset to Loc&al'), 'ldiff', None, '')
    def visualDiffToLocal(self):
        assert self._curfd.rev() is not None
        self._visualDiff([], rev=['rev(%d)' % self._curfd.rev()])

    @actionSlot(_('Diff Selected Cha&ngesets'), None, None, '')
    def visualDiffRevs(self):
        self._visualDiff([],
                         rev=['rev(%d)' % r for r in _uniqrevs(self._selfds)])

    @actionSlot(_('&Diff to Parent'), 'visualdiff', 'Ctrl+D',
                _('View file changes in external diff tool'))
    def visualDiffFile(self):
        if self._curfd.rev() is not None and self._curfd.rev() < 0:
            QMessageBox.warning(self.parent(),
                _("Cannot display visual diff"),
                _("Visual diffs are not supported for unapplied patches"))
            return
        self._visualDiff(_lcanonpaths(self._selfds), change=self._curfd.rev())

    @actionSlot(_('Diff to &Local'), 'ldiff', 'Shift+Ctrl+D',
                _('View changes to current in external diff tool'))
    def visualDiffFileToLocal(self):
        assert self._curfd.rev() is not None
        self._visualDiff(_lcanonpaths(self._selfds),
                         rev=['rev(%d)' % self._curfd.rev()])

    @actionSlot(_('Diff Selected &File Revisions'), 'visualdiff', None, '')
    def visualDiffFileRevs(self):
        self._visualDiff(_lcanonpaths(self._selfds),
                         rev=['rev(%d)' % r for r in _uniqrevs(self._selfds)])

    def _visualDiff(self, filenames, **opts):
        if self._curfd.isNull():
            return
        repo = self._fdRepoAgent().rawRepo()
        dlg = visdiff.visualdiff(repo.ui, repo, filenames, opts)
        if dlg:
            dlg.exec_()

    @actionSlot(_('&View at Revision'), 'view-at-revision', 'Shift+Ctrl+E',
                _('View file as it appeared at this revision'))
    def editFile(self):
        if self._curfd.isNull():
            return
        repo = self._fdRepoAgent().rawRepo()
        filenames = _lcanonpaths(self._selfds)
        if self._curfd.rev() is None:
            qtlib.editfiles(repo, filenames, parent=self.parent())
        else:
            ctx = self._curfd.rawContext()
            base, _ = visdiff.snapshot(repo, filenames, ctx)
            files = [os.path.join(base, filename)
                     for filename in filenames]
            qtlib.editfiles(repo, files, parent=self.parent())

    @actionSlot(_('&Save at Revision...'), None, 'Shift+Ctrl+S',
                _('Save file as it appeared at this revision'))
    def saveFile(self):
        cmdlines = []
        for fd in self._selfds:
            wfile = fd.absoluteFilePath()
            wfile, ext = os.path.splitext(os.path.basename(wfile))
            extfilter = [_("All files (*)")]
            if wfile:
                filename = "%s@%d%s" % (wfile, fd.rev(), ext)
                if ext:
                    extfilter.insert(0, "*%s" % ext)
            else:
                filename = "%s@%d" % (ext, fd.rev())

            result = QFileDialog.getSaveFileName(
                self.parent(), _("Save file to"), filename,
                ";;".join(extfilter))
            if not result:
                continue
            # checkout in working-copy line endings, etc. by --decode
            cmdlines.append(hglib.buildcmdargs(
                'cat', fd.canonicalFilePath(), rev=fd.rev(), output=result,
                decode=True))

        if cmdlines:
            self._runCommandSequence(cmdlines)

    @actionSlot(_('&Edit Local'), 'edit-file', None,
                _('Edit current file in working copy'))
    def editLocalFile(self):
        if self._curfd.isNull():
            return
        repo = self._fdRepoAgent().rawRepo()
        filenames = _lcanonpaths(self._selfds)
        qtlib.editfiles(repo, filenames, parent=self.parent())

    @actionSlot(_('&Open Local'), None, 'Shift+Ctrl+L',
                _('Edit current file in working copy'))
    def openLocalFile(self):
        if self._curfd.isNull():
            return
        repo = self._fdRepoAgent().rawRepo()
        filenames = _lcanonpaths(self._selfds)
        qtlib.openfiles(repo, filenames)

    @actionSlot(_('Copy &Path'), None, 'Shift+Ctrl+C',
                _('Copy full path of file(s) to the clipboard'))
    def copyPath(self):
        paths = [fd.absoluteFilePath() for fd in self._selfds]
        QApplication.clipboard().setText(os.linesep.join(paths))

    @actionSlot(_('&Revert to Revision...'), 'hg-revert', 'Shift+Ctrl+R',
                _('Revert file(s) to contents at this revision'))
    def revertFile(self):
        if self._curfd.isNull():
            return
        repoagent = self._fdRepoAgent()
        fileSelection = _lcanonpaths(self._selfds)
        rev = self._curfd.rev()
        if rev is None:
            repo = repoagent.rawRepo()
            rev = repo[rev].p1().rev()
        dlg = revert.RevertDialog(repoagent, fileSelection, rev,
                                  parent=self.parent())
        dlg.exec_()

    @actionSlot(_('Open S&ubrepository'), 'thg-repository-open', None,
                _('Open the selected subrepository'))
    def openSubrepo(self):
        fd = self._curfd
        if fd.subrepoType() != 'hg':
            return
        ctx = fd.rawContext()
        spath = hglib.fromunicode(fd.canonicalFilePath())
        revid = ctx.substate[spath][1]
        link = 'repo:%s?%s' % (fd.absoluteFilePath(), revid)
        self.linkActivated.emit(link)

    @actionSlot(_('E&xplore Folder'), 'system-file-manager', None,
                _('Open the selected folder in the system file manager'))
    def explore(self):
        if self._curfd.isDir():
            qtlib.openlocalurl(self._curfd.absoluteFilePath())

    @actionSlot(_('Open &Terminal'), 'utilities-terminal', None,
                _('Open a shell terminal in the selected folder'))
    def terminal(self):
        if self._curfd.isDir():
            root = hglib.fromunicode(self._curfd.absoluteFilePath())
            currentfile = hglib.fromunicode(self._curfd.filePath())
            qtlib.openshell(root, currentfile, self._ui)
