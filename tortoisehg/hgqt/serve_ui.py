# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/home/sborho/repos/thg/tortoisehg/hgqt/serve.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from tortoisehg.util.i18n import _
from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ServeDialog(object):
    def setupUi(self, ServeDialog):
        ServeDialog.setObjectName("ServeDialog")
        ServeDialog.resize(500, 400)
        self.dialog_layout = QtWidgets.QVBoxLayout(ServeDialog)
        self.dialog_layout.setObjectName("dialog_layout")
        self.top_layout = QtWidgets.QHBoxLayout()
        self.top_layout.setObjectName("top_layout")
        self.opts_layout = QtWidgets.QFormLayout()
        self.opts_layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        self.opts_layout.setObjectName("opts_layout")
        self.port_label = QtWidgets.QLabel(ServeDialog)
        self.port_label.setObjectName("port_label")
        self.opts_layout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.port_label)
        self.port_edit = QtWidgets.QSpinBox(ServeDialog)
        self.port_edit.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.port_edit.setMinimum(1)
        self.port_edit.setMaximum(65535)
        self.port_edit.setProperty("value", 8000)
        self.port_edit.setObjectName("port_edit")
        self.opts_layout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.port_edit)
        self.status_label = QtWidgets.QLabel(ServeDialog)
        self.status_label.setObjectName("status_label")
        self.opts_layout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.status_label)
        self.status_edit = QtWidgets.QLabel(ServeDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.status_edit.sizePolicy().hasHeightForWidth())
        self.status_edit.setSizePolicy(sizePolicy)
        self.status_edit.setText("")
        self.status_edit.setTextFormat(QtCore.Qt.RichText)
        self.status_edit.setOpenExternalLinks(True)
        self.status_edit.setObjectName("status_edit")
        self.opts_layout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.status_edit)
        self.top_layout.addLayout(self.opts_layout)
        self.actions_layout = QtWidgets.QVBoxLayout()
        self.actions_layout.setObjectName("actions_layout")
        self.start_button = QtWidgets.QPushButton(ServeDialog)
        self.start_button.setDefault(True)
        self.start_button.setObjectName("start_button")
        self.actions_layout.addWidget(self.start_button)
        self.stop_button = QtWidgets.QPushButton(ServeDialog)
        self.stop_button.setAutoDefault(False)
        self.stop_button.setObjectName("stop_button")
        self.actions_layout.addWidget(self.stop_button)
        spacerItem = QtWidgets.QSpacerItem(0, 5, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.actions_layout.addItem(spacerItem)
        self.settings_button = QtWidgets.QPushButton(ServeDialog)
        self.settings_button.setAutoDefault(False)
        self.settings_button.setObjectName("settings_button")
        self.actions_layout.addWidget(self.settings_button)
        self.top_layout.addLayout(self.actions_layout)
        self.top_layout.setStretch(0, 1)
        self.dialog_layout.addLayout(self.top_layout)
        self.details_tabs = QtWidgets.QTabWidget(ServeDialog)
        self.details_tabs.setObjectName("details_tabs")
        self.dialog_layout.addWidget(self.details_tabs)
        self.dialog_layout.setStretch(1, 1)
        self.port_label.setBuddy(self.port_edit)

        self.retranslateUi(ServeDialog)
        self.details_tabs.setCurrentIndex(-1)
        QtCore.QMetaObject.connectSlotsByName(ServeDialog)
        ServeDialog.setTabOrder(self.port_edit, self.start_button)
        ServeDialog.setTabOrder(self.start_button, self.stop_button)
        ServeDialog.setTabOrder(self.stop_button, self.settings_button)
        ServeDialog.setTabOrder(self.settings_button, self.details_tabs)

    def retranslateUi(self, ServeDialog):
        _translate = QtCore.QCoreApplication.translate
        ServeDialog.setWindowTitle(_('Web Server'))
        self.port_label.setText(_('Port:'))
        self.status_label.setText(_('Status:'))
        self.start_button.setText(_('Start'))
        self.stop_button.setText(_('Stop'))
        self.settings_button.setText(_('Settings'))

