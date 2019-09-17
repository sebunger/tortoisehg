# phabreview.py - TortoiseHg's dialog for posting patches to Phabricator
#
# Copyright 2018 Matt Harbison <mharbison72@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from __future__ import absolute_import

import json

from mercurial import (
    pycompat,
)

from .qtcore import (
    QBuffer,
    QIODevice,
    QSettings,
    QSortFilterProxyModel,
    Qt,
    pyqtSlot,
)
from .qtgui import (
    QDialog,
    QKeySequence,
    QListWidgetItem,
    QShortcut,
    QStandardItem,
    QStandardItemModel,
)

from ..util import hglib
from ..util.i18n import _
from . import (
    cmdcore,
    cmdui,
    lexers,
    qtlib,
)

from .hgemail import _ChangesetsModel
from .phabreview_ui import Ui_PhabReviewDialog

class user(tuple):
    '''Named tuple with user properties.'''

    __slots__ = ()

    def __new__(cls, username, realname, roles):
        return tuple.__new__(cls, (username, realname, roles))

    @property
    def username(self):
        '''username used by phabsend'''
        return self[0]

    @property
    def realname(self):
        '''friendly name of this user'''
        return self[1]

    @property
    def roles(self):
        '''the roles filled by this user'''
        return self[2]

    def __repr__(self):
        return '%s (%s)' % (self.realname, self.username)


class PhabReviewDialog(QDialog):
    """Dialog for posting patches to Phabricator"""

    def __init__(self, repoagent, revs, parent=None):
        """Create PhabReviewDialog for the given repo and revs

        :revs: List of revisions to be sent.
        """
        super(PhabReviewDialog, self).__init__(parent)
        self.setWindowFlags(Qt.Window)
        self._repoagent = repoagent
        self._cmdsession = cmdcore.nullCmdSession()
        self._rescansession = cmdcore.nullCmdSession()

        self._qui = Ui_PhabReviewDialog()
        self._qui.setupUi(self)

        proxymodel = QSortFilterProxyModel(self._qui.available_reviewer_list)
        proxymodel.setDynamicSortFilter(True)
        proxymodel.setSourceModel(QStandardItemModel())
        proxymodel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        proxymodel.sort(0)
        self.availablereviewersmodel = proxymodel

        reviewerlist = self._qui.available_reviewer_list
        reviewerlist.setModel(proxymodel)
        reviewerlist.selectionModel().selectionChanged.connect(
            self.on_available_reviewer_selection_changed)

        reviewerfilter = self._qui.reviewer_filter
        reviewerfilter.textChanged.connect(proxymodel.setFilterFixedString)

        selectedreviewerlist = self._qui.selected_reviewers_list
        selectedreviewerlist.selectionModel().selectionChanged.connect(
            self.on_reviewer_selection_changed)

        callsign = self._ui.config(b'phabricator', b'callsign')
        url = self._ui.config(b'phabricator', b'url')

        title = self.windowTitle()
        if url:
            title += hglib.tounicode(b" - " + url)
            if callsign:
                # The callsign is repo specific, so pointing to the repo in
                # Diffusion seems like a reasonable way to display both pieces
                # of Phabricator config info.
                endfmt = url.endswith(b'/') and b'r%s' or b'/r%s'
                title += hglib.tounicode(endfmt % callsign)

            self.setWindowTitle(title)

        self._initchangesets(revs)
        self._initpreviewtab()
        self._readreviewerhistory()
        self._updateforms()
        self._readsettings()
        QShortcut(QKeySequence('Ctrl+Return'), self, self.accept)
        QShortcut(QKeySequence('Ctrl+Enter'), self, self.accept)

    def closeEvent(self, event):
        self._writesettings()
        super(PhabReviewDialog, self).closeEvent(event)

    def _readsettings(self):
        s = QSettings()
        self.restoreGeometry(qtlib.readByteArray(s, 'phabsend/geom'))

    def _writesettings(self):
        s = QSettings()
        s.setValue('phabsend/geom', self.saveGeometry())

    def _reviewerhistorypath(self, withcallsign=False):
        '''Fetches the path in the settings used to store reviewer history.

        If no reviewers are stored or the configuration isn't present to find
        the reviewers, no path is returned.
        '''
        url = self._ui.config(b'phabricator', b'url')
        if not url:
            return None

        scheme, hostpath = url.split(b'://', 1)
        if hostpath.endswith(b'/'):
            hostpath = hostpath[0:-1]

        if not withcallsign:
            return 'phabsend/%s/reviewers' % hostpath

        callsign = self._ui.config(b'phabricator', b'callsign')

        if not callsign:
            return None

        return 'phabsend/%s/%s/reviewers' % (hostpath, callsign)

    def _getreviewerhistory(self):
        '''Returns a fully populated list of the users previously selected to
        perform a review for any repository on the configured server.
        '''
        path = self._reviewerhistorypath()
        if not path:
            return []

        s = QSettings()

        reviewers = []

        size = s.beginReadArray(path)
        for idx in pycompat.xrange(size):
            s.setArrayIndex(idx)
            realname = qtlib.readString(s, "realname")
            username = qtlib.readString(s, "username")
            roles = qtlib.readStringList(s, "roles")
            reviewers.append(user(username, realname, roles))
        s.endArray()

        return reviewers

    def _readreviewerhistory(self):
        '''Pre-populates the reviewer lists.

        The available reviewer list is populated with all reviewers selected
        in the past from the configured server.  The selected reviewers are
        populated with the reviewers selected for the previous review on the
        repository, as identified by the callsign.
        '''
        availablereviewers = self.availablereviewersmodel.sourceModel()

        history = {r.username: r for r in self._getreviewerhistory()}
        for reviewer in history.values():
            item = QStandardItem(pycompat.unicode(reviewer))
            item.setData(reviewer)

            # Must add to source model since setDynamicSortFilter() is True.
            availablereviewers.appendRow(item)

        # Preselect the last set of reviewers for this repository, if known.
        path = self._reviewerhistorypath(withcallsign=True)
        if path:
            s = QSettings()
            reviewers = self._qui.selected_reviewers_list
            size = s.beginReadArray(path)

            for idx in pycompat.xrange(size):
                s.setArrayIndex(idx)
                username = qtlib.readString(s, "username")
                reviewer = history.get(username)
                if reviewer:
                    witem = QListWidgetItem(pycompat.unicode(reviewer))
                    witem.setData(Qt.UserRole + 1, reviewer)
                    reviewers.addItem(witem)
            s.endArray()

    def _writereviewerhistory(self):
        '''Stores the selected reviewers persistently.

        The currently selected reviewers are combined with the existing reviewer
        history, and it is stored.  This allows the available reviewer list to
        be pre-populated with users of interest, without contacting the server.
        This cumulative history is shared across repositories that use the same
        phabricator server.
        '''
        path = self._reviewerhistorypath()
        if not path:
            return []

        # Avoid set() when eliminating duplicates, which hashes the role list
        reviewers = {r.username: r for r in self._getreviewerhistory()}
        selectedreviewers = self._qui.selected_reviewers_list

        for i in pycompat.xrange(selectedreviewers.count()):
            reviewer = selectedreviewers.item(i).data(Qt.UserRole + 1)
            reviewers[reviewer.username] = reviewer

        s = QSettings()
        s.beginWriteArray(path)

        for i, reviewer in enumerate(reviewers.values()):
            s.setArrayIndex(i)
            s.setValue("username", reviewer.username)
            s.setValue("realname", reviewer.realname)
            s.setValue("roles", reviewer.roles)

        s.endArray()

        # Store the currently selected reviewers, if tied to a repo.
        path = self._reviewerhistorypath(withcallsign=True)
        if path:
            reviewers = self._qui.selected_reviewers_list
            s.beginWriteArray(path)

            for i in pycompat.xrange(reviewers.count()):
                s.setArrayIndex(i)
                s.setValue("username",
                           reviewers.item(i).data(Qt.UserRole + 1).username)
            s.endArray()

    def _initchangesets(self, revs):
        # Posting a review amends the commits, making them hidden.  That in
        # turn would raise a FilteredRepoLookupError each time the table tries
        # to repaint after posting the review.  And that makes it almost
        # impossible to close this dialog.
        self._changesets = _ChangesetsModel(self._repo.unfiltered(),
                                            revs=revs or list(self._repo),
                                            selectedrevs=revs,
                                            parent=self)
        self._changesets.dataChanged.connect(self._updateforms)
        self._qui.changesets_view.setModel(self._changesets)

    @property
    def _repo(self):
        return self._repoagent.rawRepo()

    @property
    def _ui(self):
        return self._repo.ui

    @property
    def _revs(self):
        """Returns list of revisions to be sent"""
        return self._changesets.selectedrevs

    def _phabsendopts(self, **opts):
        """Generate opts for phabsend by form values"""
        opts['rev'] = hglib.compactrevs(self._revs)

        reviewerlist = self._qui.selected_reviewers_list
        opts['reviewer'] = [reviewerlist.item(i).data(Qt.UserRole + 1).username
                            for i in pycompat.xrange(reviewerlist.count())]

        return opts

    def _isvalid(self):
        """Filled all required values?"""
        if not self._revs:
            return False

        return True

    @pyqtSlot()
    def _updateforms(self):
        """Update availability of form widgets"""
        valid = self._isvalid()
        self._qui.send_button.setEnabled(valid)
        self._qui.main_tabs.setTabEnabled(self._previewtabindex(), valid)

    def accept(self):
        opts = self._phabsendopts()
        cmdline = hglib.buildcmdargs('phabsend', **opts)
        cmd = cmdui.CmdSessionDialog(self)
        cmd.setWindowTitle(_('Posting Review'))
        cmd.setLogVisible(True)
        cmd.setSession(self._repoagent.runCommand(cmdline, self))
        if cmd.exec_() == 0:
            self._writereviewerhistory()

    def _initpreviewtab(self):
        def initqsci(w):
            w.setUtf8(True)
            w.setReadOnly(True)
            w.setMarginWidth(1, 0)  # hide area for line numbers
            self.lexer = lex = lexers.difflexer(self)
            fh = qtlib.getfont('fontdiff')
            fh.changed.connect(self.forwardFont)
            lex.setFont(fh.font())
            w.setLexer(lex)
            # TODO: better way to setup diff lexer

        initqsci(self._qui.preview_edit)

        self._qui.main_tabs.currentChanged.connect(self._refreshpreviewtab)
        self._refreshpreviewtab(self._qui.main_tabs.currentIndex())

    def forwardFont(self, font):
        if self.lexer:
            self.lexer.setFont(font)

    @pyqtSlot(int)
    def _refreshpreviewtab(self, index):
        """Generate preview text if current tab is preview"""
        if self._previewtabindex() != index:
            return

        self._qui.preview_edit.clear()

        cmdline = hglib.buildcmdargs('export', git=True,
                                     rev=hglib.compactrevs(self._revs))
        self._cmdsession = sess = self._repoagent.runCommand(cmdline)
        sess.setCaptureOutput(True)
        sess.commandFinished.connect(self._updatepreview)

    @pyqtSlot()
    def _updatepreview(self):
        preview = self._qui.preview_edit
        exported = hglib.tounicode(str(self._cmdsession.readAll()))

        callsign = self._ui.config(b'phabricator', b'callsign')
        if not callsign:
            callsign = b'Not Configured!'
        url = self._ui.config(b'phabricator', b'url')
        if not url:
            url = b'Not Configured!'

        reviewerlist = self._qui.selected_reviewers_list
        role = Qt.UserRole + 1

        reviewers = [reviewerlist.item(i).data(role).username
                     for i in pycompat.xrange(reviewerlist.count())]
        if reviewers:
            reviewers = u', '.join(reviewers)
        else:
            reviewers = u'None'

        preview.append(u'Server:    %s\n' % hglib.tounicode(url))
        preview.append(u'Callsign:  %s\n' % hglib.tounicode(callsign))
        preview.append(u'Reviewers: %s\n' % reviewers)
        preview.append(u'\n\n')

        preview.append(exported)

    def _previewtabindex(self):
        """Index of preview tab"""
        return self._qui.main_tabs.indexOf(self._qui.preview_tab)

    def _appendavailablereviewers(self, conduitresult):
        """Process the result of a conduit call, and add reviewers to the
        available reviewers list.
        """
        availablereviewers = self.availablereviewersmodel.sourceModel()

        # A single user JSON entry looks like this:
        #
        #   {
        #     "attachments": {},
        #     "fields": {
        #       "dateCreated": 1544870724,
        #       "dateModified": 1544870725,
        #       "policy": {
        #         "edit": "no-one",
        #         "view": "public"
        #       },
        #       "realName": "UserName LastName",
        #       "roles": [
        #         "admin",
        #         "verified",
        #         "approved",
        #         "activated"   <-- or "disabled" for deactivated user
        #       ],
        #       "username": "user"
        #     },
        #     "id": 1,
        #     "phid": "PHID-USER-5f2bb6z25cceqs266inw",
        #     "type": "USER"
        #   }
        #
        # Additional roles include "list" for mailing list entries.

        for data in conduitresult.get('data', {}):
            fields = data.get('fields', {})
            realname = fields.get('realName')
            username = fields.get('username')
            roles = fields.get('roles', [])

            if not realname or not username:
                continue

            u = user(username, realname, roles)
            item = QStandardItem(pycompat.unicode(u))
            item.setData(u)

            # Must add to source model since setDynamicSortFilter() is True.
            availablereviewers.appendRow(item)

    def _queryreviewers(self, after):
        """Issues the command to query the users, and arranges to have
        _updateavailablereviewers() called on completion.  ``after`` is the
        cursor value from the result of the last command, or None at the start
        of the sequence.
        """
        buf = QBuffer()

        # phabsend doesn't seem to complain about sending reviews to deactivate
        # users, but filter them out anyway.  It also doesn't seem to make much
        # sense to send a review request to a bot.
        if after is not None:
            buf.setData(b'''{
                "constraints": {
                    "isBot": false,
                    "isDisabled": false
                },
                "after": %s
            }''' % after)
        else:
            buf.setData(b'''{
                "constraints": {
                    "isBot": false,
                    "isDisabled": false
                }
            }''')

        buf.open(QIODevice.ReadOnly)

        cmdline = hglib.buildcmdargs('debugcallconduit', 'user.search')
        self._rescansession = sess = self._repoagent.runCommand(cmdline)
        sess.setCaptureOutput(True)
        sess.setInputDevice(buf)
        sess.commandFinished.connect(self._updateavailablereviewers)

    @pyqtSlot()
    def on_rescan_button_clicked(self):
        availablereviewers = self.availablereviewersmodel.sourceModel()

        availablereviewers.clear()
        self._qui.rescan_button.setEnabled(False)

        self._queryreviewers(None)

    @pyqtSlot()
    def _updateavailablereviewers(self):

        exitcode = self._rescansession.exitCode()

        if exitcode == 0:
            output = hglib.tounicode(str(self._rescansession.readAll()))

            results = json.loads(output)
            self._appendavailablereviewers(results)

            # The default behavior is to batch 100 users at a time, and requires
            # a second call, with the 'after' value specified in the cursor of
            # the response to pick up the rest.  'after' is None at the end of
            # the sequence.  To test the continuation logic, `"limit": 1` can be
            # added to the request parameters.
            cursor = results.get('cursor')
            if cursor and 'after' in cursor:
                after = cursor.get('after')
                if after:
                    self._queryreviewers(hglib.fromunicode(after))
                    return
        else:
            cmdui.errorMessageBox(self._rescansession, self,
                                  "Phabricator Error")

        # Done, either by error or completing the sequence.
        self._qui.rescan_button.setEnabled(True)

    @pyqtSlot()
    def on_available_reviewer_selection_changed(self):
        view = self._qui.available_reviewer_list
        self._qui.addreviewer_button.setEnabled(bool(view.selectedIndexes()))

    @pyqtSlot()
    def on_reviewer_selection_changed(self):
        view = self._qui.selected_reviewers_list
        self._qui.removereviewer_button.setEnabled(bool(view.selectedIndexes()))

    @pyqtSlot()
    def on_addreviewer_button_clicked(self):
        """Populates the selected reviewers list when the ">" button is clicked.
        """
        reviewers = self._qui.selected_reviewers_list
        proxymodel = self.availablereviewersmodel
        model = proxymodel.sourceModel()

        for i in self._qui.available_reviewer_list.selectedIndexes():
            item = model.item(proxymodel.mapToSource(i).row())
            if not reviewers.findItems(item.text(), Qt.MatchExactly):
                witem = QListWidgetItem(item.text())
                witem.setData(Qt.UserRole + 1, item.data())
                reviewers.addItem(witem)

    @pyqtSlot()
    def on_removereviewer_button_clicked(self):
        """Removes items from the selected reviewers list when the "<" button is
        clicked.
        """
        reviewers = self._qui.selected_reviewers_list
        for i in reviewers.selectedItems():
            reviewers.takeItem(reviewers.row(i))

    @pyqtSlot()
    def on_selectall_button_clicked(self):
        self._changesets.selectAll()

    @pyqtSlot()
    def on_selectnone_button_clicked(self):
        self._changesets.selectNone()
