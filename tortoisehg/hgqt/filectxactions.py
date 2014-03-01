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

from tortoisehg.hgqt import qtlib, revert, visdiff, customtools
from tortoisehg.hgqt import filedata, filedialogs
from tortoisehg.hgqt.i18n import _
from tortoisehg.util import hglib

_actionsbytype = {
    'subrepo': ['opensubrepo', 'explore', 'terminal', 'copypath', None,
                'revert'],
    'file': ['diff', 'ldiff', None, 'edit', 'save', None, 'ledit', 'lopen',
             'copypath', None, 'revert', None, 'navigate', 'diffnavigate'],
    'dir': ['diff', 'ldiff', None, 'revert', None, 'filter',
            None, 'explore', 'terminal', 'copypath'],
    }

def _lcanonpaths(fds):
    return [hglib.fromunicode(e.canonicalFilePath()) for e in fds]


class FilectxActions(QObject):
    """Container for repository file actions"""

    linkActivated = pyqtSignal(unicode)
    filterRequested = pyqtSignal(QString)
    """Ask the repowidget to change its revset filter"""

    runCustomCommandRequested = pyqtSignal(str, list)

    def __init__(self, repoagent, parent=None):
        super(FilectxActions, self).__init__(parent)
        if parent is not None and not isinstance(parent, QWidget):
            raise ValueError('parent must be a QWidget')

        self._repoagent = repoagent
        repo = repoagent.rawRepo()
        self._curfd = filedata.createNullData(repo)
        self._selfds = []

        self._nav_dialogs = qtlib.DialogKeeper(FilectxActions._createnavdialog,
                                               FilectxActions._gennavdialogkey,
                                               self)

        self._actions = {}
        for name, desc, icon, key, tip, cb in [
            ('navigate', _('File &History'), 'hg-log', 'Shift+Return',
             _('Show the history of the selected file'), self.navigate),
            ('filter', _('Folder &History'), 'hg-log', None,
             _('Show the history of the selected file'), self.filterfile),
            ('diffnavigate', _('Co&mpare File Revisions'), 'compare-files', None,
             _('Compare revisions of the selected file'), self.diffNavigate),
            ('diff', _('&Diff to Parent'), 'visualdiff', 'Ctrl+D',
             _('View file changes in external diff tool'), self.vdiff),
            ('ldiff', _('Diff to &Local'), 'ldiff', 'Shift+Ctrl+D',
             _('View changes to current in external diff tool'),
             self.vdifflocal),
            ('edit', _('&View at Revision'), 'view-at-revision', 'Shift+Ctrl+E',
             _('View file as it appeared at this revision'), self.editfile),
            ('save', _('&Save at Revision...'), None, 'Shift+Ctrl+S',
             _('Save file as it appeared at this revision'), self.savefile),
            ('ledit', _('&Edit Local'), 'edit-file', None,
             _('Edit current file in working copy'), self.editlocal),
            ('lopen', _('&Open Local'), '', 'Shift+Ctrl+L',
             _('Edit current file in working copy'), self.openlocal),
            ('copypath', _('Copy &Path'), '', 'Shift+Ctrl+C',
             _('Copy full path of file(s) to the clipboard'), self.copypath),
            ('revert', _('&Revert to Revision...'), 'hg-revert', 'Shift+Ctrl+R',
             _('Revert file(s) to contents at this revision'),
             self.revertfile),
            ('opensubrepo', _('Open S&ubrepository'), 'thg-repository-open',
             None, _('Open the selected subrepository'),
             self.opensubrepo),
            ('explore', _('E&xplore Folder'), 'system-file-manager',
             None, _('Open the selected folder in the system file manager'),
             self.explore),
            ('terminal', _('Open &Terminal'), 'utilities-terminal', None,
             _('Open a shell terminal in the selected folder'),
             self.terminal),
            ]:
            act = QAction(desc, self)
            if icon:
                act.setIcon(qtlib.geticon(icon))
            if key:
                act.setShortcut(key)
            if tip:
                act.setStatusTip(tip)
            if cb:
                act.triggered.connect(cb)
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
        real = self._curfd.rev() is not None and self._curfd.rev() >= 0
        wd = self._curfd.rev() is None
        singlefile = len(self._selfds) == 1 and not self._curfd.isDir()
        for act in ['ldiff', 'edit', 'save']:
            self._actions[act].setEnabled(real)
        for act in ['diff', 'revert']:
            self._actions[act].setEnabled(real or wd)
        for act in ['navigate', 'diffnavigate']:
            self._actions[act].setEnabled(real and singlefile)
        for act in ['opensubrepo']:
            self._actions[act].setEnabled(self._curfd.subrepoType() == 'hg')

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

    def createMenu(self, parent=None):
        """New menu for the current selection if available; otherwise None"""
        if self._curfd.isNull():
            return

        # Subrepos and regular items have different context menus
        if self._curfd.subrepoType():
            return self._createMenuFor('subrepo', parent)
        elif self._curfd.isDir():
            return self._createMenuFor('dir', parent)
        else:
            return self._createMenuFor('file', parent)

    def _createMenuFor(self, key, parent):
        contextmenu = QMenu(parent)
        for act in _actionsbytype[key]:
            if act:
                contextmenu.addAction(self._actions[act])
            else:
                contextmenu.addSeparator()
        self._setupCustomSubmenu(contextmenu)
        return contextmenu

    def _setupCustomSubmenu(self, menu):
        def make(text, func, types=None, icon=None, inmenu=None):
            action = inmenu.addAction(text)
            if icon:
                action.setIcon(qtlib.geticon(icon))
            return action

        menu.addSeparator()
        customtools.addCustomToolsSubmenu(menu, self._ui,
            location='workbench.filelist.custom-menu',
            make=make,
            slot=self._runCustomCommandByMenu)

    @pyqtSlot(QAction)
    def _runCustomCommandByMenu(self, action):
        files = [fd.filePath() for fd in self._selfds
                 if os.path.exists(fd.absoluteFilePath())]
        if not files:
            qtlib.WarningMsgBox(_('File(s) not found'),
                _('The selected files do not exist in the working directory'))
            return
        self.runCustomCommandRequested.emit(
            str(action.data().toString()), files)

    def navigate(self):
        self._navigate(filedialogs.FileLogDialog)

    def diffNavigate(self):
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

    def filterfile(self):
        """Ask to only show the revisions in which files on that folder are
        present"""
        if self._curfd.isNull():
            return
        pats = ["file('path:%s')" % fd.filePath() for fd in self._selfds]
        self.filterRequested.emit(' or '.join(pats))

    def vdiff(self):
        if self._curfd.rev() is not None and self._curfd.rev() < 0:
            QMessageBox.warning(self.parent(),
                _("Cannot display visual diff"),
                _("Visual diffs are not supported for unapplied patches"))
            return
        self._visualDiff(change=self._curfd.rev())

    def vdifflocal(self):
        assert self._curfd.rev() is not None
        self._visualDiff(rev=['rev(%d)' % self._curfd.rev()])

    def _visualDiff(self, **opts):
        if self._curfd.isNull():
            return
        repo = self._fdRepoAgent().rawRepo()
        filenames = _lcanonpaths(self._selfds)
        dlg = visdiff.visualdiff(repo.ui, repo, filenames, opts)
        if dlg:
            dlg.exec_()

    def editfile(self):
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

    def savefile(self):
        if self._curfd.isNull():
            return
        repo = self._fdRepoAgent().rawRepo()
        filenames = _lcanonpaths(self._selfds)
        rev = self._curfd.rev()
        qtlib.savefiles(repo, filenames, rev, parent=self.parent())

    def editlocal(self):
        if self._curfd.isNull():
            return
        repo = self._fdRepoAgent().rawRepo()
        filenames = _lcanonpaths(self._selfds)
        qtlib.editfiles(repo, filenames, parent=self.parent())

    def openlocal(self):
        if self._curfd.isNull():
            return
        repo = self._fdRepoAgent().rawRepo()
        filenames = _lcanonpaths(self._selfds)
        qtlib.openfiles(repo, filenames)

    def copypath(self):
        paths = [fd.absoluteFilePath() for fd in self._selfds]
        QApplication.clipboard().setText(os.linesep.join(paths))

    def revertfile(self):
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

    def opensubrepo(self):
        fd = self._curfd
        if fd.subrepoType() != 'hg':
            return
        ctx = fd.rawContext()
        spath = hglib.fromunicode(fd.canonicalFilePath())
        revid = ctx.substate[spath][1]
        link = 'repo:%s?%s' % (fd.absoluteFilePath(), revid)
        self.linkActivated.emit(link)

    def explore(self):
        if self._curfd.isDir():
            qtlib.openlocalurl(self._curfd.absoluteFilePath())

    def terminal(self):
        if self._curfd.isDir():
            root = hglib.fromunicode(self._curfd.absoluteFilePath())
            currentfile = hglib.fromunicode(self._curfd.filePath())
            qtlib.openshell(root, currentfile, self._ui)
