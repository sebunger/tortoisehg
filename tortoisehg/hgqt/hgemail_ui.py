# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/sborho/repos/thg/tortoisehg/hgqt/hgemail.ui'
#
# Created: Wed Aug  5 20:33:10 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from tortoisehg.util.i18n import _
from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_EmailDialog(object):
    def setupUi(self, EmailDialog):
        EmailDialog.setObjectName(_fromUtf8("EmailDialog"))
        EmailDialog.resize(660, 519)
        EmailDialog.setSizeGripEnabled(True)
        self.verticalLayout_5 = QtGui.QVBoxLayout(EmailDialog)
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        self.main_tabs = QtGui.QTabWidget(EmailDialog)
        self.main_tabs.setDocumentMode(False)
        self.main_tabs.setTabsClosable(False)
        self.main_tabs.setMovable(False)
        self.main_tabs.setObjectName(_fromUtf8("main_tabs"))
        self.edit_tab = QtGui.QWidget()
        self.edit_tab.setObjectName(_fromUtf8("edit_tab"))
        self.gridLayout = QtGui.QGridLayout(self.edit_tab)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.envelope_box = QtGui.QGroupBox(self.edit_tab)
        self.envelope_box.setTitle(_fromUtf8(""))
        self.envelope_box.setObjectName(_fromUtf8("envelope_box"))
        self.formLayout = QtGui.QFormLayout(self.envelope_box)
        self.formLayout.setFieldGrowthPolicy(QtGui.QFormLayout.ExpandingFieldsGrow)
        self.formLayout.setObjectName(_fromUtf8("formLayout"))
        self.to_label = QtGui.QLabel(self.envelope_box)
        self.to_label.setObjectName(_fromUtf8("to_label"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.LabelRole, self.to_label)
        self.to_edit = QtGui.QComboBox(self.envelope_box)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.to_edit.sizePolicy().hasHeightForWidth())
        self.to_edit.setSizePolicy(sizePolicy)
        self.to_edit.setEditable(True)
        self.to_edit.setInsertPolicy(QtGui.QComboBox.InsertAtTop)
        self.to_edit.setObjectName(_fromUtf8("to_edit"))
        self.formLayout.setWidget(0, QtGui.QFormLayout.FieldRole, self.to_edit)
        self.cc_label = QtGui.QLabel(self.envelope_box)
        self.cc_label.setObjectName(_fromUtf8("cc_label"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.LabelRole, self.cc_label)
        self.cc_edit = QtGui.QComboBox(self.envelope_box)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cc_edit.sizePolicy().hasHeightForWidth())
        self.cc_edit.setSizePolicy(sizePolicy)
        self.cc_edit.setEditable(True)
        self.cc_edit.setInsertPolicy(QtGui.QComboBox.InsertAtTop)
        self.cc_edit.setObjectName(_fromUtf8("cc_edit"))
        self.formLayout.setWidget(1, QtGui.QFormLayout.FieldRole, self.cc_edit)
        self.from_label = QtGui.QLabel(self.envelope_box)
        self.from_label.setObjectName(_fromUtf8("from_label"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.LabelRole, self.from_label)
        self.from_edit = QtGui.QComboBox(self.envelope_box)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.from_edit.sizePolicy().hasHeightForWidth())
        self.from_edit.setSizePolicy(sizePolicy)
        self.from_edit.setEditable(True)
        self.from_edit.setInsertPolicy(QtGui.QComboBox.InsertAtTop)
        self.from_edit.setObjectName(_fromUtf8("from_edit"))
        self.formLayout.setWidget(2, QtGui.QFormLayout.FieldRole, self.from_edit)
        self.inreplyto_label = QtGui.QLabel(self.envelope_box)
        self.inreplyto_label.setObjectName(_fromUtf8("inreplyto_label"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.LabelRole, self.inreplyto_label)
        self.inreplyto_edit = QtGui.QLineEdit(self.envelope_box)
        self.inreplyto_edit.setObjectName(_fromUtf8("inreplyto_edit"))
        self.formLayout.setWidget(3, QtGui.QFormLayout.FieldRole, self.inreplyto_edit)
        self.flag_label = QtGui.QLabel(self.envelope_box)
        self.flag_label.setObjectName(_fromUtf8("flag_label"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.LabelRole, self.flag_label)
        self.flag_edit = QtGui.QComboBox(self.envelope_box)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.flag_edit.sizePolicy().hasHeightForWidth())
        self.flag_edit.setSizePolicy(sizePolicy)
        self.flag_edit.setEditable(True)
        self.flag_edit.setInsertPolicy(QtGui.QComboBox.InsertAtTop)
        self.flag_edit.setObjectName(_fromUtf8("flag_edit"))
        self.formLayout.setWidget(4, QtGui.QFormLayout.FieldRole, self.flag_edit)
        self.gridLayout.addWidget(self.envelope_box, 0, 0, 1, 1)
        self.options_edit = QtGui.QGroupBox(self.edit_tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.options_edit.sizePolicy().hasHeightForWidth())
        self.options_edit.setSizePolicy(sizePolicy)
        self.options_edit.setTitle(_fromUtf8(""))
        self.options_edit.setObjectName(_fromUtf8("options_edit"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.options_edit)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.patch_frame = QtGui.QFrame(self.options_edit)
        self.patch_frame.setFrameShape(QtGui.QFrame.NoFrame)
        self.patch_frame.setFrameShadow(QtGui.QFrame.Raised)
        self.patch_frame.setObjectName(_fromUtf8("patch_frame"))
        self.verticalLayout = QtGui.QVBoxLayout(self.patch_frame)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.hgpatch_radio = QtGui.QRadioButton(self.patch_frame)
        self.hgpatch_radio.setObjectName(_fromUtf8("hgpatch_radio"))
        self.verticalLayout.addWidget(self.hgpatch_radio)
        self.gitpatch_radio = QtGui.QRadioButton(self.patch_frame)
        self.gitpatch_radio.setObjectName(_fromUtf8("gitpatch_radio"))
        self.verticalLayout.addWidget(self.gitpatch_radio)
        self.plainpatch_radio = QtGui.QRadioButton(self.patch_frame)
        self.plainpatch_radio.setObjectName(_fromUtf8("plainpatch_radio"))
        self.verticalLayout.addWidget(self.plainpatch_radio)
        self.bundle_radio = QtGui.QRadioButton(self.patch_frame)
        self.bundle_radio.setObjectName(_fromUtf8("bundle_radio"))
        self.verticalLayout.addWidget(self.bundle_radio)
        self.verticalLayout_4.addWidget(self.patch_frame)
        self.extra_frame = QtGui.QFrame(self.options_edit)
        self.extra_frame.setFrameShape(QtGui.QFrame.NoFrame)
        self.extra_frame.setFrameShadow(QtGui.QFrame.Raised)
        self.extra_frame.setObjectName(_fromUtf8("extra_frame"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.extra_frame)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.body_check = QtGui.QCheckBox(self.extra_frame)
        self.body_check.setEnabled(True)
        self.body_check.setChecked(True)
        self.body_check.setObjectName(_fromUtf8("body_check"))
        self.horizontalLayout.addWidget(self.body_check)
        self.attach_check = QtGui.QCheckBox(self.extra_frame)
        self.attach_check.setObjectName(_fromUtf8("attach_check"))
        self.horizontalLayout.addWidget(self.attach_check)
        self.inline_check = QtGui.QCheckBox(self.extra_frame)
        self.inline_check.setObjectName(_fromUtf8("inline_check"))
        self.horizontalLayout.addWidget(self.inline_check)
        self.diffstat_check = QtGui.QCheckBox(self.extra_frame)
        self.diffstat_check.setObjectName(_fromUtf8("diffstat_check"))
        self.horizontalLayout.addWidget(self.diffstat_check)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout_4.addWidget(self.extra_frame)
        self.gridLayout.addWidget(self.options_edit, 0, 1, 1, 1)
        self.writeintro_check = QtGui.QCheckBox(self.edit_tab)
        self.writeintro_check.setObjectName(_fromUtf8("writeintro_check"))
        self.gridLayout.addWidget(self.writeintro_check, 1, 0, 1, 2)
        self.intro_changesets_splitter = QtGui.QSplitter(self.edit_tab)
        self.intro_changesets_splitter.setOrientation(QtCore.Qt.Vertical)
        self.intro_changesets_splitter.setObjectName(_fromUtf8("intro_changesets_splitter"))
        self.intro_box = QtGui.QGroupBox(self.intro_changesets_splitter)
        self.intro_box.setTitle(_fromUtf8(""))
        self.intro_box.setObjectName(_fromUtf8("intro_box"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.intro_box)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.subject_layout = QtGui.QHBoxLayout()
        self.subject_layout.setObjectName(_fromUtf8("subject_layout"))
        self.subject_label = QtGui.QLabel(self.intro_box)
        self.subject_label.setObjectName(_fromUtf8("subject_label"))
        self.subject_layout.addWidget(self.subject_label)
        self.subject_edit = QtGui.QComboBox(self.intro_box)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.subject_edit.sizePolicy().hasHeightForWidth())
        self.subject_edit.setSizePolicy(sizePolicy)
        self.subject_edit.setEditable(True)
        self.subject_edit.setInsertPolicy(QtGui.QComboBox.InsertAtTop)
        self.subject_edit.setObjectName(_fromUtf8("subject_edit"))
        self.subject_layout.addWidget(self.subject_edit)
        self.verticalLayout_2.addLayout(self.subject_layout)
        self.body_edit = QtGui.QPlainTextEdit(self.intro_box)
        font = QtGui.QFont()
        font.setFamily(_fromUtf8("Monospace"))
        self.body_edit.setFont(font)
        self.body_edit.setObjectName(_fromUtf8("body_edit"))
        self.verticalLayout_2.addWidget(self.body_edit)
        self.changesets_box = QtGui.QGroupBox(self.intro_changesets_splitter)
        self.changesets_box.setObjectName(_fromUtf8("changesets_box"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.changesets_box)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.changesets_view = QtGui.QTreeView(self.changesets_box)
        self.changesets_view.setIndentation(0)
        self.changesets_view.setRootIsDecorated(False)
        self.changesets_view.setItemsExpandable(False)
        self.changesets_view.setObjectName(_fromUtf8("changesets_view"))
        self.verticalLayout_3.addWidget(self.changesets_view)
        self.selectallnone_layout = QtGui.QHBoxLayout()
        self.selectallnone_layout.setObjectName(_fromUtf8("selectallnone_layout"))
        self.selectall_button = QtGui.QPushButton(self.changesets_box)
        self.selectall_button.setObjectName(_fromUtf8("selectall_button"))
        self.selectallnone_layout.addWidget(self.selectall_button)
        self.selectnone_button = QtGui.QPushButton(self.changesets_box)
        self.selectnone_button.setObjectName(_fromUtf8("selectnone_button"))
        self.selectallnone_layout.addWidget(self.selectnone_button)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.selectallnone_layout.addItem(spacerItem1)
        self.verticalLayout_3.addLayout(self.selectallnone_layout)
        self.gridLayout.addWidget(self.intro_changesets_splitter, 2, 0, 1, 2)
        self.main_tabs.addTab(self.edit_tab, _fromUtf8(""))
        self.preview_tab = QtGui.QWidget()
        self.preview_tab.setObjectName(_fromUtf8("preview_tab"))
        self.gridLayout_2 = QtGui.QGridLayout(self.preview_tab)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.preview_edit = Qsci.QsciScintilla(self.preview_tab)
        self.preview_edit.setObjectName(_fromUtf8("preview_edit"))
        self.gridLayout_2.addWidget(self.preview_edit, 0, 0, 1, 1)
        self.main_tabs.addTab(self.preview_tab, _fromUtf8(""))
        self.verticalLayout_5.addWidget(self.main_tabs)
        self.dialogbuttons_layout = QtGui.QHBoxLayout()
        self.dialogbuttons_layout.setObjectName(_fromUtf8("dialogbuttons_layout"))
        self.settings_button = QtGui.QPushButton(EmailDialog)
        self.settings_button.setToolTip(_fromUtf8(""))
        self.settings_button.setDefault(False)
        self.settings_button.setObjectName(_fromUtf8("settings_button"))
        self.dialogbuttons_layout.addWidget(self.settings_button)
        spacerItem2 = QtGui.QSpacerItem(25, 19, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.dialogbuttons_layout.addItem(spacerItem2)
        self.send_button = QtGui.QPushButton(EmailDialog)
        self.send_button.setEnabled(False)
        self.send_button.setDefault(False)
        self.send_button.setObjectName(_fromUtf8("send_button"))
        self.dialogbuttons_layout.addWidget(self.send_button)
        self.close_button = QtGui.QPushButton(EmailDialog)
        self.close_button.setEnabled(True)
        self.close_button.setDefault(True)
        self.close_button.setObjectName(_fromUtf8("close_button"))
        self.dialogbuttons_layout.addWidget(self.close_button)
        self.verticalLayout_5.addLayout(self.dialogbuttons_layout)
        self.to_label.setBuddy(self.to_edit)
        self.cc_label.setBuddy(self.cc_edit)
        self.from_label.setBuddy(self.from_edit)
        self.inreplyto_label.setBuddy(self.inreplyto_edit)
        self.flag_label.setBuddy(self.flag_edit)
        self.subject_label.setBuddy(self.subject_edit)

        self.retranslateUi(EmailDialog)
        self.main_tabs.setCurrentIndex(0)
        QtCore.QObject.connect(self.writeintro_check, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.intro_box.setVisible)
        QtCore.QObject.connect(self.send_button, QtCore.SIGNAL(_fromUtf8("clicked()")), EmailDialog.accept)
        QtCore.QObject.connect(self.close_button, QtCore.SIGNAL(_fromUtf8("clicked()")), EmailDialog.close)
        QtCore.QObject.connect(self.writeintro_check, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), self.subject_edit.setFocus)
        QtCore.QMetaObject.connectSlotsByName(EmailDialog)
        EmailDialog.setTabOrder(self.main_tabs, self.to_edit)
        EmailDialog.setTabOrder(self.to_edit, self.cc_edit)
        EmailDialog.setTabOrder(self.cc_edit, self.from_edit)
        EmailDialog.setTabOrder(self.from_edit, self.inreplyto_edit)
        EmailDialog.setTabOrder(self.inreplyto_edit, self.flag_edit)
        EmailDialog.setTabOrder(self.flag_edit, self.hgpatch_radio)
        EmailDialog.setTabOrder(self.hgpatch_radio, self.gitpatch_radio)
        EmailDialog.setTabOrder(self.gitpatch_radio, self.plainpatch_radio)
        EmailDialog.setTabOrder(self.plainpatch_radio, self.bundle_radio)
        EmailDialog.setTabOrder(self.bundle_radio, self.body_check)
        EmailDialog.setTabOrder(self.body_check, self.attach_check)
        EmailDialog.setTabOrder(self.attach_check, self.inline_check)
        EmailDialog.setTabOrder(self.inline_check, self.diffstat_check)
        EmailDialog.setTabOrder(self.diffstat_check, self.writeintro_check)
        EmailDialog.setTabOrder(self.writeintro_check, self.subject_edit)
        EmailDialog.setTabOrder(self.subject_edit, self.body_edit)
        EmailDialog.setTabOrder(self.body_edit, self.changesets_view)
        EmailDialog.setTabOrder(self.changesets_view, self.send_button)
        EmailDialog.setTabOrder(self.send_button, self.preview_edit)
        EmailDialog.setTabOrder(self.preview_edit, self.settings_button)

    def retranslateUi(self, EmailDialog):
        EmailDialog.setWindowTitle(_('Email'))
        self.to_label.setText(_('To:'))
        self.cc_label.setText(_('Cc:'))
        self.from_label.setText(_('From:'))
        self.inreplyto_label.setText(_('In-Reply-To:'))
        self.inreplyto_edit.setToolTip(_('Message identifier to reply to, for threading'))
        self.flag_label.setText(_('Flag:'))
        self.hgpatch_radio.setWhatsThis(_('Hg patches (as generated by export command) are compatible with most patch programs.  They include a header which contains the most important changeset metadata.'))
        self.hgpatch_radio.setText(_('Send changesets as Hg patches'))
        self.gitpatch_radio.setWhatsThis(_('Git patches can describe binary files, copies, and permission changes, but recipients may not be able to use them if they are not using git or Mercurial.'))
        self.gitpatch_radio.setText(_('Use extended (git) patch format'))
        self.plainpatch_radio.setWhatsThis(_('Stripping Mercurial header removes username and parent information.  Only useful if recipient is not using Mercurial (and does not like to see the headers).'))
        self.plainpatch_radio.setText(_('Plain, do not prepend Hg header'))
        self.bundle_radio.setWhatsThis(_('Bundles store complete changesets in binary form. Upstream users can pull from them. This is the safest way to send changes to recipient Mercurial users.'))
        self.bundle_radio.setText(_('Send single binary bundle, not patches'))
        self.body_check.setToolTip(_('send patches as part of the email body'))
        self.body_check.setText(_('body'))
        self.attach_check.setToolTip(_('send patches as attachments'))
        self.attach_check.setText(_('attach'))
        self.inline_check.setToolTip(_('send patches as inline attachments'))
        self.inline_check.setText(_('inline'))
        self.diffstat_check.setToolTip(_('add diffstat output to messages'))
        self.diffstat_check.setText(_('diffstat'))
        self.writeintro_check.setWhatsThis(_('Patch series description is sent in initial summary email with [PATCH 0 of N] subject.  It should describe the effects of the entire patch series.  When emailing a bundle, these fields make up the message subject and body. Flags is a comma separated list of tags which are inserted into the message subject prefix.'))
        self.writeintro_check.setText(_('Write patch series (bundle) description'))
        self.subject_label.setText(_('Subject:'))
        self.changesets_box.setTitle(_('Changesets'))
        self.selectall_button.setText(_('Select &All'))
        self.selectnone_button.setText(_('Select &None'))
        self.main_tabs.setTabText(self.main_tabs.indexOf(self.edit_tab), _('Edit'))
        self.main_tabs.setTabText(self.main_tabs.indexOf(self.preview_tab), _('Preview'))
        self.settings_button.setText(_('&Settings'))
        self.send_button.setText(_('Send &Email'))
        self.close_button.setText(_('&Close'))

from PyQt4 import Qsci
