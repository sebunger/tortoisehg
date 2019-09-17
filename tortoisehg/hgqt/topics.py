# topics.py - Topic dialog for TortoiseHg
#
# Copyright 2010 Michal De Wildt <michael.dewildt@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from __future__ import absolute_import

from mercurial import error

from .qtcore import (
    Qt,
    pyqtSlot,
)
from .qtgui import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QLabel,
    QLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from mercurial import (
    pycompat,
)

from ..util import hglib
from ..util.obsoleteutil import first_known_successors
from ..util.i18n import _
from . import (
    cmdcore,
    qtlib,
)

class TopicsDialog(QDialog):

    def __init__(self, repoagent, rev, parent=None):
        super(TopicsDialog, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() &
                            ~Qt.WindowContextHelpButtonHint)
        self._repoagent = repoagent
        repo = repoagent.rawRepo()
        self._cmdsession = cmdcore.nullCmdSession()
        self.rev = rev

        # base layout box
        base = QVBoxLayout()
        base.setSpacing(0)
        base.setContentsMargins(*(0,)*4)
        base.setSizeConstraint(QLayout.SetMinAndMaxSize)
        self.setLayout(base)

        # main layout grid
        formwidget = QWidget(self)
        formwidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        form = QFormLayout(fieldGrowthPolicy=QFormLayout.AllNonFixedFieldsGrow)
        formwidget.setLayout(form)
        base.addWidget(formwidget)

        if rev:
            form.addRow(_('Revision:'), QLabel('%d (%s)' % (rev, repo[rev])))

        # topic combo
        self.topicsCombo = QComboBox()
        self.topicsCombo.setEditable(True)
        self.topicsCombo.setMinimumContentsLength(30)  # cut long name
        self.topicsCombo.currentIndexChanged.connect(self.topicTextChanged)
        self.topicsCombo.editTextChanged.connect(self.topicTextChanged)
        qtlib.allowCaseChangingInput(self.topicsCombo)
        form.addRow(_('Topic:'), self.topicsCombo)

        # bottom buttons
        BB = QDialogButtonBox
        bbox = QDialogButtonBox()
        self.addBtn = bbox.addButton(_('&Add'), BB.ActionRole)
        self.removeBtn = bbox.addButton(_('&Remove'), BB.ActionRole)
        self.renameBtn = bbox.addButton(_('&Rename'), BB.ActionRole)
        bbox.addButton(BB.Close)
        bbox.rejected.connect(self.reject)
        form.addRow(bbox)

        self.addBtn.clicked.connect(self.add_topic)
        self.removeBtn.clicked.connect(self.remove_topic)
        self.renameBtn.clicked.connect(self.rename_topic)

        # horizontal separator
        self.sep = QFrame()
        self.sep.setFrameShadow(QFrame.Sunken)
        self.sep.setFrameShape(QFrame.HLine)
        self.layout().addWidget(self.sep)

        # status line
        self.status = qtlib.StatusLabel()
        self.status.setContentsMargins(4, 2, 4, 4)
        self.layout().addWidget(self.status)
        self._finishmsg = None

        # dialog setting
        self.setWindowTitle(_('Topic - %s') % repoagent.displayName())
        self.setWindowIcon(qtlib.geticon('hg-topics'))

        # prepare to show
        self.clear_status()
        self.refresh()
        self._repoagent.repositoryChanged.connect(self.refresh)
        self.topicsCombo.setFocus()
        self.topicTextChanged()

    @property
    def repo(self):
        return self._repoagent.rawRepo()

    def _allTopics(self):
        return (pycompat.maplist(hglib.tounicode, self.repo._topics)
                if self.repo._topics else [])

    @pyqtSlot()
    def refresh(self):
        """Update display on dialog with recent repo data"""
        # add topics to drop-down list

        cur = self.topicsCombo.currentText()
        self.topicsCombo.clear()
        self.topicsCombo.addItems(sorted(self._allTopics()))
        if cur and not self._is_wd:
            self.topicsCombo.setEditText(cur)
        elif self._is_wd:
            self.topicsCombo.setEditText('')
        else:
            cs_topic = self._current_topic
            if self.repo.currenttopic == cs_topic:
                tp = hglib.tounicode(self.repo.currenttopic)
                self.topicsCombo.setEditText(tp)
            elif cs_topic:
                tp = hglib.tounicode(cs_topic)
                self.topicsCombo.setEditText(tp)
            else:
                self.topicTextChanged()

    @pyqtSlot()
    def topicTextChanged(self):
        topic = self.topicsCombo.currentText()
        topiclocal = hglib.fromunicode(topic)
        current_topic = self._current_topic
        if (self.repo._topics and topiclocal in self.repo._topics
            and not self._is_wd):
            if topiclocal != current_topic:
                self.addBtn.setEnabled(False)
                self.removeBtn.setEnabled(False)
                self.renameBtn.setEnabled(True)
            else:
                self.addBtn.setEnabled(False)
                self.removeBtn.setEnabled(True)
                self.renameBtn.setEnabled(False)
        else:
            self.addBtn.setEnabled(bool(topic))
            self.removeBtn.setEnabled(False)
            self.renameBtn.setEnabled(False)

    @property
    def _is_wd(self):
        try:
            ctx = self.repo[self.rev]
        except error.FilteredRepoLookupError as exc:
            self._set_successor(exc)
            ctx = self.repo[self.rev]
        return ctx.rev() is None

    @property
    def _current_topic(self):
        try:
            ctx = self.repo[self.rev]
        except error.FilteredRepoLookupError as exc:
            self._set_successor(exc)
            ctx = self.repo[self.rev]
        return ctx.topic()

    def _set_successor(self, exc=error.FilteredRepoLookupError):
        repo = self.repo.unfiltered()
        ctx = repo[self.rev]
        if ctx.extinct():
            changes = [x for x in first_known_successors(ctx)]
            if changes:
                self.rev = changes[0].rev()
            else:
                raise exc
        else:
            raise exc

    def setTopicName(self, name):
        self.topicsCombo.setEditText(name)

    def set_status(self, text, icon=None):
        self.status.setVisible(True)
        self.sep.setVisible(True)
        self.status.set_status(text, icon)

    def clear_status(self):
        self.status.setHidden(True)
        self.sep.setHidden(True)

    def _runTopics(self, *args, **opts):
        self._finishmsg = opts.pop('finishmsg')
        cmdline = hglib.buildcmdargs('topics', *args, **opts)
        self._cmdsession = sess = self._repoagent.runCommand(cmdline, self)
        sess.commandFinished.connect(self._onTopicsFinished)

    @pyqtSlot(int)
    def _onTopicsFinished(self, ret):
        if ret == 0:
            self.topicsCombo.clearEditText()
            self.set_status(self._finishmsg, True)
        else:
            self.set_status(self._cmdsession.errorString(), False)

    @pyqtSlot()
    def add_topic(self):
        topic = pycompat.unicode(self.topicsCombo.currentText())
        if topic in self._allTopics():
            self.set_status(_('A topic named "%s" already exists') %
                            topic, False)
            return

        finishmsg = _("Topic '%s' has been added") % topic
        rev = None
        if self.rev:
            rev = self.rev
        self._runTopics(topic, rev=rev, finishmsg=finishmsg)

    @pyqtSlot()
    def remove_topic(self):
        topic = pycompat.unicode(self.topicsCombo.currentText())
        if topic not in self._allTopics():
            self.set_status(_("Topic '%s' does not exist") % topic, False)
            return

        finishmsg = _("Topic '%s' has been removed") % topic
        rev = None
        if self.rev:
            rev = self.rev
        self._runTopics(rev=rev, clear=True, finishmsg=finishmsg)

    @pyqtSlot()
    def rename_topic(self):
        topic = pycompat.unicode(self.topicsCombo.currentText())
        finishmsg = (_("Topic '%s' has been renamed to %s")
                     % (self._current_topic, topic))
        rev = None
        if self.rev:
            rev = self.rev
        self._runTopics(topic, rev=rev, finishmsg=finishmsg)
