# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/sborho/repos/thg/tortoisehg/hgqt/postreview.ui'
#
# Created: Mon Nov  9 10:56:48 2015
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

class Ui_PostReviewDialog(object):
    def setupUi(self, PostReviewDialog):
        PostReviewDialog.setObjectName(_fromUtf8("PostReviewDialog"))
        PostReviewDialog.resize(660, 459)
        self.verticalLayout_5 = QtGui.QVBoxLayout(PostReviewDialog)
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.tab_widget = QtGui.QTabWidget(PostReviewDialog)
        self.tab_widget.setMaximumSize(QtCore.QSize(16777215, 110))
        self.tab_widget.setObjectName(_fromUtf8("tab_widget"))
        self.post_review_tab = QtGui.QWidget()
        self.post_review_tab.setObjectName(_fromUtf8("post_review_tab"))
        self.formLayout_2 = QtGui.QFormLayout(self.post_review_tab)
        self.formLayout_2.setObjectName(_fromUtf8("formLayout_2"))
        self.repo_id_label = QtGui.QLabel(self.post_review_tab)
        self.repo_id_label.setObjectName(_fromUtf8("repo_id_label"))
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.LabelRole, self.repo_id_label)
        self.repo_id_combo = QtGui.QComboBox(self.post_review_tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.repo_id_combo.sizePolicy().hasHeightForWidth())
        self.repo_id_combo.setSizePolicy(sizePolicy)
        self.repo_id_combo.setEditable(False)
        self.repo_id_combo.setInsertPolicy(QtGui.QComboBox.InsertAtTop)
        self.repo_id_combo.setObjectName(_fromUtf8("repo_id_combo"))
        self.formLayout_2.setWidget(0, QtGui.QFormLayout.FieldRole, self.repo_id_combo)
        self.summary_label = QtGui.QLabel(self.post_review_tab)
        self.summary_label.setObjectName(_fromUtf8("summary_label"))
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.LabelRole, self.summary_label)
        self.summary_edit = QtGui.QComboBox(self.post_review_tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.summary_edit.sizePolicy().hasHeightForWidth())
        self.summary_edit.setSizePolicy(sizePolicy)
        self.summary_edit.setEditable(True)
        self.summary_edit.setInsertPolicy(QtGui.QComboBox.InsertAtTop)
        self.summary_edit.setObjectName(_fromUtf8("summary_edit"))
        self.formLayout_2.setWidget(1, QtGui.QFormLayout.FieldRole, self.summary_edit)
        self.tab_widget.addTab(self.post_review_tab, _fromUtf8(""))
        self.update_review_tab = QtGui.QWidget()
        self.update_review_tab.setObjectName(_fromUtf8("update_review_tab"))
        self.formLayout_3 = QtGui.QFormLayout(self.update_review_tab)
        self.formLayout_3.setObjectName(_fromUtf8("formLayout_3"))
        self.review_id_label = QtGui.QLabel(self.update_review_tab)
        self.review_id_label.setObjectName(_fromUtf8("review_id_label"))
        self.formLayout_3.setWidget(0, QtGui.QFormLayout.LabelRole, self.review_id_label)
        self.review_id_combo = QtGui.QComboBox(self.update_review_tab)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.review_id_combo.sizePolicy().hasHeightForWidth())
        self.review_id_combo.setSizePolicy(sizePolicy)
        self.review_id_combo.setEditable(False)
        self.review_id_combo.setInsertPolicy(QtGui.QComboBox.InsertAtTop)
        self.review_id_combo.setObjectName(_fromUtf8("review_id_combo"))
        self.formLayout_3.setWidget(0, QtGui.QFormLayout.FieldRole, self.review_id_combo)
        self.update_fields = QtGui.QCheckBox(self.update_review_tab)
        self.update_fields.setObjectName(_fromUtf8("update_fields"))
        self.formLayout_3.setWidget(1, QtGui.QFormLayout.FieldRole, self.update_fields)
        self.tab_widget.addTab(self.update_review_tab, _fromUtf8(""))
        self.verticalLayout.addWidget(self.tab_widget)
        self.options_group = QtGui.QGroupBox(PostReviewDialog)
        self.options_group.setObjectName(_fromUtf8("options_group"))
        self.gridLayout = QtGui.QGridLayout(self.options_group)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.outgoing_changes_check = QtGui.QCheckBox(self.options_group)
        self.outgoing_changes_check.setObjectName(_fromUtf8("outgoing_changes_check"))
        self.gridLayout.addWidget(self.outgoing_changes_check, 0, 0, 1, 1)
        self.branch_check = QtGui.QCheckBox(self.options_group)
        self.branch_check.setObjectName(_fromUtf8("branch_check"))
        self.gridLayout.addWidget(self.branch_check, 0, 1, 1, 1)
        self.publish_immediately_check = QtGui.QCheckBox(self.options_group)
        self.publish_immediately_check.setObjectName(_fromUtf8("publish_immediately_check"))
        self.gridLayout.addWidget(self.publish_immediately_check, 2, 0, 1, 1)
        self.verticalLayout.addWidget(self.options_group)
        self.changesets_box = QtGui.QGroupBox(PostReviewDialog)
        self.changesets_box.setEnabled(True)
        self.changesets_box.setToolTip(_fromUtf8(""))
        self.changesets_box.setObjectName(_fromUtf8("changesets_box"))
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.changesets_box)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.changesets_view = QtGui.QTreeView(self.changesets_box)
        self.changesets_view.setIndentation(0)
        self.changesets_view.setRootIsDecorated(False)
        self.changesets_view.setItemsExpandable(False)
        self.changesets_view.setObjectName(_fromUtf8("changesets_view"))
        self.changesets_view.header().setHighlightSections(False)
        self.changesets_view.header().setSortIndicatorShown(False)
        self.verticalLayout_3.addWidget(self.changesets_view)
        self.verticalLayout.addWidget(self.changesets_box)
        self.verticalLayout_5.addLayout(self.verticalLayout)
        self.dialogbuttons_layout = QtGui.QHBoxLayout()
        self.dialogbuttons_layout.setObjectName(_fromUtf8("dialogbuttons_layout"))
        self.settings_button = QtGui.QPushButton(PostReviewDialog)
        self.settings_button.setToolTip(_fromUtf8(""))
        self.settings_button.setDefault(False)
        self.settings_button.setObjectName(_fromUtf8("settings_button"))
        self.dialogbuttons_layout.addWidget(self.settings_button)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.dialogbuttons_layout.addItem(spacerItem)
        self.progress_bar = QtGui.QProgressBar(PostReviewDialog)
        self.progress_bar.setMinimumSize(QtCore.QSize(200, 0))
        font = QtGui.QFont()
        font.setKerning(True)
        self.progress_bar.setFont(font)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.setProperty("value", -1)
        self.progress_bar.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setOrientation(QtCore.Qt.Horizontal)
        self.progress_bar.setInvertedAppearance(False)
        self.progress_bar.setTextDirection(QtGui.QProgressBar.TopToBottom)
        self.progress_bar.setObjectName(_fromUtf8("progress_bar"))
        self.dialogbuttons_layout.addWidget(self.progress_bar)
        self.progress_label = QtGui.QLabel(PostReviewDialog)
        self.progress_label.setObjectName(_fromUtf8("progress_label"))
        self.dialogbuttons_layout.addWidget(self.progress_label)
        spacerItem1 = QtGui.QSpacerItem(0, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.dialogbuttons_layout.addItem(spacerItem1)
        self.post_review_button = QtGui.QPushButton(PostReviewDialog)
        self.post_review_button.setEnabled(False)
        self.post_review_button.setDefault(False)
        self.post_review_button.setObjectName(_fromUtf8("post_review_button"))
        self.dialogbuttons_layout.addWidget(self.post_review_button)
        self.close_button = QtGui.QPushButton(PostReviewDialog)
        self.close_button.setEnabled(True)
        self.close_button.setDefault(True)
        self.close_button.setObjectName(_fromUtf8("close_button"))
        self.dialogbuttons_layout.addWidget(self.close_button)
        self.verticalLayout_5.addLayout(self.dialogbuttons_layout)
        self.repo_id_label.setBuddy(self.repo_id_combo)
        self.summary_label.setBuddy(self.summary_edit)
        self.review_id_label.setBuddy(self.review_id_combo)

        self.retranslateUi(PostReviewDialog)
        self.tab_widget.setCurrentIndex(0)
        QtCore.QObject.connect(self.post_review_button, QtCore.SIGNAL(_fromUtf8("clicked()")), PostReviewDialog.accept)
        QtCore.QObject.connect(self.settings_button, QtCore.SIGNAL(_fromUtf8("clicked()")), PostReviewDialog.onSettingsButtonClicked)
        QtCore.QObject.connect(self.close_button, QtCore.SIGNAL(_fromUtf8("clicked()")), PostReviewDialog.close)
        QtCore.QObject.connect(self.outgoing_changes_check, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), PostReviewDialog.outgoingChangesCheckToggle)
        QtCore.QObject.connect(self.branch_check, QtCore.SIGNAL(_fromUtf8("toggled(bool)")), PostReviewDialog.branchCheckToggle)
        QtCore.QObject.connect(self.tab_widget, QtCore.SIGNAL(_fromUtf8("currentChanged(int)")), PostReviewDialog.tabChanged)
        QtCore.QMetaObject.connectSlotsByName(PostReviewDialog)
        PostReviewDialog.setTabOrder(self.changesets_view, self.post_review_button)
        PostReviewDialog.setTabOrder(self.post_review_button, self.settings_button)

    def retranslateUi(self, PostReviewDialog):
        PostReviewDialog.setWindowTitle(_('Review Board'))
        self.repo_id_label.setText(_('Repository ID:'))
        self.summary_label.setText(_('Summary:'))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.post_review_tab), _('Post Review'))
        self.review_id_label.setText(_('Review ID:'))
        self.update_fields.setText(_('Update the fields of this existing request'))
        self.tab_widget.setTabText(self.tab_widget.indexOf(self.update_review_tab), _('Update Review'))
        self.options_group.setTitle(_('Options'))
        self.outgoing_changes_check.setText(_('Create diff with all outgoing changes'))
        self.branch_check.setText(_('Create diff with all changes on this branch'))
        self.publish_immediately_check.setText(_('Publish request immediately'))
        self.changesets_box.setTitle(_('Changesets'))
        self.settings_button.setText(_('&Settings'))
        self.progress_bar.setFormat(_('%p%'))
        self.progress_label.setText(_('Connecting to Review Board...'))
        self.post_review_button.setText(_('Post &Review'))
        self.close_button.setText(_('&Close'))

