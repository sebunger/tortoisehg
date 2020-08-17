# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/yuya/work/hghacks/thg/tortoisehg/hgqt/phabreview.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from tortoisehg.util.i18n import _
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_PhabReviewDialog(object):
    def setupUi(self, PhabReviewDialog):
        PhabReviewDialog.setObjectName("PhabReviewDialog")
        PhabReviewDialog.resize(818, 604)
        PhabReviewDialog.setSizeGripEnabled(True)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(PhabReviewDialog)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.main_tabs = QtWidgets.QTabWidget(PhabReviewDialog)
        self.main_tabs.setDocumentMode(False)
        self.main_tabs.setTabsClosable(False)
        self.main_tabs.setMovable(False)
        self.main_tabs.setObjectName("main_tabs")
        self.edit_tab = QtWidgets.QWidget()
        self.edit_tab.setObjectName("edit_tab")
        self.gridLayout = QtWidgets.QGridLayout(self.edit_tab)
        self.gridLayout.setObjectName("gridLayout")
        self.reviewers_box = QtWidgets.QGroupBox(self.edit_tab)
        self.reviewers_box.setObjectName("reviewers_box")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.reviewers_box)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.available_reviewers_group = QtWidgets.QGroupBox(self.reviewers_box)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.available_reviewers_group.sizePolicy().hasHeightForWidth())
        self.available_reviewers_group.setSizePolicy(sizePolicy)
        self.available_reviewers_group.setToolTip("")
        self.available_reviewers_group.setObjectName("available_reviewers_group")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.available_reviewers_group)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.gridLayout_5 = QtWidgets.QGridLayout()
        self.gridLayout_5.setObjectName("gridLayout_5")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_5.addItem(spacerItem, 2, 2, 1, 1)
        self.rescan_button = QtWidgets.QPushButton(self.available_reviewers_group)
        self.rescan_button.setObjectName("rescan_button")
        self.gridLayout_5.addWidget(self.rescan_button, 2, 1, 1, 1)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout_5.addItem(spacerItem1, 2, 0, 1, 1)
        self.reviewer_filter = QtWidgets.QLineEdit(self.available_reviewers_group)
        self.reviewer_filter.setObjectName("reviewer_filter")
        self.gridLayout_5.addWidget(self.reviewer_filter, 0, 0, 1, 3)
        self.available_reviewer_list = QtWidgets.QListView(self.available_reviewers_group)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.available_reviewer_list.sizePolicy().hasHeightForWidth())
        self.available_reviewer_list.setSizePolicy(sizePolicy)
        self.available_reviewer_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.available_reviewer_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.available_reviewer_list.setObjectName("available_reviewer_list")
        self.gridLayout_5.addWidget(self.available_reviewer_list, 1, 0, 1, 3)
        self.verticalLayout_2.addLayout(self.gridLayout_5)
        self.horizontalLayout.addWidget(self.available_reviewers_group)
        self.widget = QtWidgets.QWidget(self.reviewers_box)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem2)
        self.addreviewer_button = QtWidgets.QPushButton(self.widget)
        self.addreviewer_button.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addreviewer_button.sizePolicy().hasHeightForWidth())
        self.addreviewer_button.setSizePolicy(sizePolicy)
        self.addreviewer_button.setMinimumSize(QtCore.QSize(0, 0))
        self.addreviewer_button.setIconSize(QtCore.QSize(0, 0))
        self.addreviewer_button.setObjectName("addreviewer_button")
        self.verticalLayout.addWidget(self.addreviewer_button)
        self.removereviewer_button = QtWidgets.QPushButton(self.widget)
        self.removereviewer_button.setEnabled(False)
        self.removereviewer_button.setObjectName("removereviewer_button")
        self.verticalLayout.addWidget(self.removereviewer_button)
        spacerItem3 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem3)
        self.horizontalLayout.addWidget(self.widget)
        self.selected_reviewers_group = QtWidgets.QGroupBox(self.reviewers_box)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selected_reviewers_group.sizePolicy().hasHeightForWidth())
        self.selected_reviewers_group.setSizePolicy(sizePolicy)
        self.selected_reviewers_group.setToolTip("")
        self.selected_reviewers_group.setObjectName("selected_reviewers_group")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.selected_reviewers_group)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.selected_reviewers_list = QtWidgets.QListWidget(self.selected_reviewers_group)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.selected_reviewers_list.sizePolicy().hasHeightForWidth())
        self.selected_reviewers_list.setSizePolicy(sizePolicy)
        self.selected_reviewers_list.setObjectName("selected_reviewers_list")
        self.horizontalLayout_2.addWidget(self.selected_reviewers_list)
        self.horizontalLayout.addWidget(self.selected_reviewers_group)
        self.gridLayout.addWidget(self.reviewers_box, 0, 0, 1, 1)
        self.changesets_box = QtWidgets.QGroupBox(self.edit_tab)
        self.changesets_box.setObjectName("changesets_box")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.changesets_box)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.changesets_view = QtWidgets.QTreeView(self.changesets_box)
        self.changesets_view.setIndentation(0)
        self.changesets_view.setRootIsDecorated(False)
        self.changesets_view.setItemsExpandable(False)
        self.changesets_view.setObjectName("changesets_view")
        self.verticalLayout_3.addWidget(self.changesets_view)
        self.selectallnone_layout = QtWidgets.QHBoxLayout()
        self.selectallnone_layout.setObjectName("selectallnone_layout")
        self.selectall_button = QtWidgets.QPushButton(self.changesets_box)
        self.selectall_button.setObjectName("selectall_button")
        self.selectallnone_layout.addWidget(self.selectall_button)
        self.selectnone_button = QtWidgets.QPushButton(self.changesets_box)
        self.selectnone_button.setObjectName("selectnone_button")
        self.selectallnone_layout.addWidget(self.selectnone_button)
        spacerItem4 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.selectallnone_layout.addItem(spacerItem4)
        self.verticalLayout_3.addLayout(self.selectallnone_layout)
        self.gridLayout.addWidget(self.changesets_box, 1, 0, 1, 1)
        self.main_tabs.addTab(self.edit_tab, "")
        self.preview_tab = QtWidgets.QWidget()
        self.preview_tab.setObjectName("preview_tab")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.preview_tab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.preview_edit = Qsci.QsciScintilla(self.preview_tab)
        self.preview_edit.setObjectName("preview_edit")
        self.gridLayout_2.addWidget(self.preview_edit, 0, 0, 1, 1)
        self.main_tabs.addTab(self.preview_tab, "")
        self.verticalLayout_5.addWidget(self.main_tabs)
        self.dialogbuttons_layout = QtWidgets.QHBoxLayout()
        self.dialogbuttons_layout.setObjectName("dialogbuttons_layout")
        self.settings_button = QtWidgets.QPushButton(PhabReviewDialog)
        self.settings_button.setEnabled(False)
        self.settings_button.setToolTip("")
        self.settings_button.setDefault(False)
        self.settings_button.setObjectName("settings_button")
        self.dialogbuttons_layout.addWidget(self.settings_button)
        spacerItem5 = QtWidgets.QSpacerItem(25, 19, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.dialogbuttons_layout.addItem(spacerItem5)
        self.send_button = QtWidgets.QPushButton(PhabReviewDialog)
        self.send_button.setEnabled(False)
        self.send_button.setDefault(False)
        self.send_button.setObjectName("send_button")
        self.dialogbuttons_layout.addWidget(self.send_button)
        self.close_button = QtWidgets.QPushButton(PhabReviewDialog)
        self.close_button.setEnabled(True)
        self.close_button.setDefault(True)
        self.close_button.setObjectName("close_button")
        self.dialogbuttons_layout.addWidget(self.close_button)
        self.verticalLayout_5.addLayout(self.dialogbuttons_layout)

        self.retranslateUi(PhabReviewDialog)
        self.main_tabs.setCurrentIndex(0)
        self.send_button.clicked.connect(PhabReviewDialog.accept)
        self.close_button.clicked.connect(PhabReviewDialog.close)
        QtCore.QMetaObject.connectSlotsByName(PhabReviewDialog)
        PhabReviewDialog.setTabOrder(self.main_tabs, self.rescan_button)
        PhabReviewDialog.setTabOrder(self.rescan_button, self.reviewer_filter)
        PhabReviewDialog.setTabOrder(self.reviewer_filter, self.available_reviewer_list)
        PhabReviewDialog.setTabOrder(self.available_reviewer_list, self.addreviewer_button)
        PhabReviewDialog.setTabOrder(self.addreviewer_button, self.selected_reviewers_list)
        PhabReviewDialog.setTabOrder(self.selected_reviewers_list, self.removereviewer_button)
        PhabReviewDialog.setTabOrder(self.removereviewer_button, self.changesets_view)
        PhabReviewDialog.setTabOrder(self.changesets_view, self.selectall_button)
        PhabReviewDialog.setTabOrder(self.selectall_button, self.selectnone_button)
        PhabReviewDialog.setTabOrder(self.selectnone_button, self.settings_button)
        PhabReviewDialog.setTabOrder(self.settings_button, self.close_button)
        PhabReviewDialog.setTabOrder(self.close_button, self.send_button)

    def retranslateUi(self, PhabReviewDialog):
        _translate = QtCore.QCoreApplication.translate
        PhabReviewDialog.setWindowTitle(_("Phabricator"))
        self.reviewers_box.setTitle(_("Reviewers"))
        self.available_reviewers_group.setTitle(_("Available"))
        self.rescan_button.setToolTip(_("Fetch the reviewer list from the server"))
        self.rescan_button.setText(_("Rescan"))
        self.reviewer_filter.setToolTip(_("Filter the available reviewers"))
        self.reviewer_filter.setPlaceholderText(_("Reviewer Filter"))
        self.available_reviewer_list.setToolTip(_("Reviewers available on the server"))
        self.addreviewer_button.setToolTip(_("Chose the selected available reviewers"))
        self.addreviewer_button.setText(_(">"))
        self.removereviewer_button.setToolTip(_("Remove the selected reviewers"))
        self.removereviewer_button.setText(_("<"))
        self.selected_reviewers_group.setTitle(_("Selected"))
        self.selected_reviewers_list.setToolTip(_("These users will be notified of the review"))
        self.selected_reviewers_list.setSortingEnabled(True)
        self.changesets_box.setTitle(_("Changesets"))
        self.selectall_button.setText(_("Select &All"))
        self.selectnone_button.setText(_("Select &None"))
        self.main_tabs.setTabText(self.main_tabs.indexOf(self.edit_tab), _("Edit"))
        self.main_tabs.setTabText(self.main_tabs.indexOf(self.preview_tab), _("Preview"))
        self.settings_button.setText(_("&Settings"))
        self.send_button.setText(_("Post &Review"))
        self.close_button.setText(_("&Close"))

from PyQt5 import Qsci
