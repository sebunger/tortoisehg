# repository.py - menu to change repository attributes
#
# Copyright 2014 Yuya Nishihara <yuya@tcha.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

from tortoisehg.hgqt.qtcore import (
    pyqtSlot,
)
from tortoisehg.hgqt.qtgui import (
    QFileDialog,
)

from mercurial import error

from tortoisehg.util import hglib

from . import dbgutil

class RepositoryMenuActions(dbgutil.BaseMenuActions):
    """Set up debug menu for RepoAgent"""

    def _setupMenu(self, menu):
        a = menu.addAction('Open &Bundle...')
        a.triggered.connect(self.openBundle)
        a = menu.addAction('Open &Union...')
        a.triggered.connect(self.openUnion)
        a = menu.addAction('&Clear Overlay')
        a.triggered.connect(self.clearOverlay)

    def _findRepoAgent(self):
        rw = self._findRepoWidget()
        return rw._repoagent

    @pyqtSlot()
    def openBundle(self):
        path, _filter = QFileDialog.getOpenFileName(
            self._parentWidget(), 'Open Bundle', '',
            'Bundle files (*.hg);;All files (*)')
        if path:
            self._setOverlay('bundle:%s' % path)

    @pyqtSlot()
    def openUnion(self):
        path = QFileDialog.getExistingDirectory(
            self._parentWidget(), 'Open Union Repository')
        if path:
            self._setOverlay('union:%s' % path)

    def _setOverlay(self, path):
        repoagent = self._findRepoAgent()
        try:
            repoagent.setOverlay(path)
        except error.RepoError as inst:
            self._warning('Repository Error', hglib.tounicode(str(inst)))

    @pyqtSlot()
    def clearOverlay(self):
        repoagent = self._findRepoAgent()
        repoagent.clearOverlay()
