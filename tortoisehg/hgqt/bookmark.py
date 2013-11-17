# bookmark.py - Bookmark dialog for TortoiseHg
#
# Copyright 2010 Michal De Wildt <michael.dewildt@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from tortoisehg.util import hglib
from tortoisehg.hgqt.i18n import _
from tortoisehg.hgqt import cmdcore, qtlib

class BookmarkDialog(QDialog):

    def __init__(self, repoagent, rev, parent=None):
        super(BookmarkDialog, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() & \
                            ~Qt.WindowContextHelpButtonHint)
        self._repoagent = repoagent
        repo = repoagent.rawRepo()
        self._cmdsession = cmdcore.nullCmdSession()
        self.rev = rev
        self.node = repo[rev].node()

        # base layout box
        base = QVBoxLayout()
        base.setSpacing(0)
        base.setContentsMargins(*(0,)*4)
        base.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(base)

        box = QVBoxLayout()
        box.setSpacing(8)
        box.setContentsMargins(*(8,)*4)
        self.layout().addLayout(box)

        ## main layout grid
        form = QFormLayout(fieldGrowthPolicy=QFormLayout.AllNonFixedFieldsGrow)
        box.addLayout(form)

        form.addRow(_('Revision:'), QLabel('%d (%s)' % (rev, repo[rev])))

        ### bookmark combo
        self.bookmarkCombo = QComboBox()
        self.bookmarkCombo.setEditable(True)
        self.bookmarkCombo.currentIndexChanged.connect(self.bookmarkTextChanged)
        self.bookmarkCombo.editTextChanged.connect(self.bookmarkTextChanged)
        qtlib.allowCaseChangingInput(self.bookmarkCombo)
        form.addRow(_('Bookmark:'), self.bookmarkCombo)

        ### Rename input
        self.newNameEdit = QLineEdit()
        self.newNameEdit.textEdited.connect(self.bookmarkTextChanged)
        form.addRow(_('New Name:'), self.newNameEdit)

        ### Activate checkbox
        self.activateCheckBox = QCheckBox()
        if self.node == self.repo['.'].node():
            self.activateCheckBox.setChecked(True)
        else:
            self.activateCheckBox.setChecked(False)
            self.activateCheckBox.setEnabled(False)
        form.addRow(_('Activate:'), self.activateCheckBox)

        ## bottom buttons
        BB = QDialogButtonBox
        bbox = QDialogButtonBox()
        self.addBtn = bbox.addButton(_('&Add'), BB.ActionRole)
        self.renameBtn = bbox.addButton(_('Re&name'), BB.ActionRole)
        self.removeBtn = bbox.addButton(_('&Remove'), BB.ActionRole)
        self.moveBtn = bbox.addButton(_('&Move'), BB.ActionRole)
        bbox.addButton(BB.Close)
        bbox.rejected.connect(self.reject)
        box.addWidget(bbox)

        self.addBtn.clicked.connect(self.add_bookmark)
        self.renameBtn.clicked.connect(self.rename_bookmark)
        self.removeBtn.clicked.connect(self.remove_bookmark)
        self.moveBtn.clicked.connect(self.move_bookmark)

        ## horizontal separator
        self.sep = QFrame()
        self.sep.setFrameShadow(QFrame.Sunken)
        self.sep.setFrameShape(QFrame.HLine)
        self.layout().addWidget(self.sep)

        ## status line
        self.status = qtlib.StatusLabel()
        self.status.setContentsMargins(4, 2, 4, 4)
        self.layout().addWidget(self.status)
        self._finishmsg = None

        # dialog setting
        self.setWindowTitle(_('Bookmark - %s') % self.repo.displayname)
        self.setWindowIcon(qtlib.geticon('hg-bookmarks'))

        # prepare to show
        self.clear_status()
        self.refresh()
        self._repoagent.repositoryChanged.connect(self.refresh)
        self.bookmarkCombo.setFocus()
        self.bookmarkTextChanged()

    @property
    def repo(self):
        return self._repoagent.rawRepo()

    def _allBookmarks(self):
        return map(hglib.tounicode, self.repo._bookmarks)

    @pyqtSlot()
    def refresh(self):
        """ update display on dialog with recent repo data """
        # add bookmarks to drop-down list
        cur = self.bookmarkCombo.currentText()
        self.bookmarkCombo.clear()
        self.bookmarkCombo.addItems(sorted(self._allBookmarks()))
        if cur:
            self.bookmarkCombo.setEditText(cur)
        else:
            ctx = self.repo[self.rev]
            cs_bookmarks = ctx.bookmarks()
            if self.repo._bookmarkcurrent in cs_bookmarks:
                bm = hglib.tounicode(self.repo._bookmarkcurrent)
                self.bookmarkCombo.setEditText(bm)
            elif cs_bookmarks:
                bm = hglib.tounicode(cs_bookmarks[0])
                self.bookmarkCombo.setEditText(bm)
            else:
                self.bookmarkTextChanged()

    @pyqtSlot()
    def bookmarkTextChanged(self):
        bookmark = self.bookmarkCombo.currentText()
        bookmarklocal = hglib.fromunicode(bookmark)
        if bookmarklocal in self.repo._bookmarks:
            curnode = self.repo._bookmarks[bookmarklocal]
            self.addBtn.setEnabled(False)
            self.newNameEdit.setEnabled(True)
            self.removeBtn.setEnabled(True)
            self.renameBtn.setEnabled(bool(self.newNameEdit.text()))
            self.moveBtn.setEnabled(self.node != curnode)
        else:
            self.addBtn.setEnabled(bool(bookmark))
            self.removeBtn.setEnabled(False)
            self.moveBtn.setEnabled(False)
            self.renameBtn.setEnabled(False)
            self.newNameEdit.setEnabled(False)

    def setBookmarkName(self, name):
        self.bookmarkCombo.setEditText(name)

    def set_status(self, text, icon=None):
        self.status.setShown(True)
        self.sep.setShown(True)
        self.status.set_status(text, icon)

    def clear_status(self):
        self.status.setHidden(True)
        self.sep.setHidden(True)

    def _runBookmark(self, *args, **opts):
        self._finishmsg = opts.pop('finishmsg')
        cmdline = hglib.buildcmdargs('bookmarks', *args, **opts)
        self._cmdsession = sess = self._repoagent.runCommand(cmdline, self)
        sess.commandFinished.connect(self._onBookmarkFinished)

    @pyqtSlot(int)
    def _onBookmarkFinished(self, ret):
        if ret == 0:
            self.bookmarkCombo.clearEditText()
            self.newNameEdit.setText('')
            self.set_status(self._finishmsg, True)
        else:
            self.set_status(self._cmdsession.errorString(), False)

    @pyqtSlot()
    def add_bookmark(self):
        bookmark = unicode(self.bookmarkCombo.currentText())
        if bookmark in self._allBookmarks():
            self.set_status(_('A bookmark named "%s" already exists') %
                            bookmark, False)
            return

        finishmsg = _("Bookmark '%s' has been added") % bookmark
        rev = None
        if not self.activateCheckBox.isChecked():
            rev = self.rev
        self._runBookmark(bookmark, rev=rev, finishmsg=finishmsg)

    @pyqtSlot()
    def move_bookmark(self):
        bookmark = unicode(self.bookmarkCombo.currentText())
        if bookmark not in self._allBookmarks():
            self.set_status(_('Bookmark named "%s" does not exist') %
                            bookmark, False)
            return

        finishmsg = _("Bookmark '%s' has been moved") % bookmark
        rev = None
        if not self.activateCheckBox.isChecked():
            rev = self.rev
        self._runBookmark(bookmark, rev=rev, force=True, finishmsg=finishmsg)

    @pyqtSlot()
    def remove_bookmark(self):
        bookmark = unicode(self.bookmarkCombo.currentText())
        if bookmark not in self._allBookmarks():
            self.set_status(_("Bookmark '%s' does not exist") % bookmark, False)
            return

        finishmsg = _("Bookmark '%s' has been removed") % bookmark
        self._runBookmark(bookmark, delete=True, finishmsg=finishmsg)

    @pyqtSlot()
    def rename_bookmark(self):
        name = unicode(self.bookmarkCombo.currentText())
        if name not in self._allBookmarks():
            self.set_status(_("Bookmark '%s' does not exist") % name, False)
            return

        newname = unicode(self.newNameEdit.text())
        if newname in self._allBookmarks():
            self.set_status(_('A bookmark named "%s" already exists') %
                            newname, False)
            return

        finishmsg = (_("Bookmark '%s' has been renamed to '%s'")
                     % (name, newname))
        self._runBookmark(name, newname, rename=True, finishmsg=finishmsg)
