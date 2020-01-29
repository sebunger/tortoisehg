# widgets.py - menu to find invisible widgets and gc issues
#
# Copyright 2013 Yuya Nishihara <yuya@tcha.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from __future__ import absolute_import

import gc
import pprint
import re
import weakref

from tortoisehg.hgqt import qtlib
from tortoisehg.hgqt.qtcore import (
    QObject,
    QTimer,
    pyqtSignal,
    pyqtSlot,
)
from tortoisehg.hgqt.qtgui import (
    QAction,
    QApplication,
    QCheckBox,
    QDesktopWidget,
    QDialog,
    QDialogButtonBox,
    QMenu,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from . import dbgutil

def invisibleWindows():
    """List of invisible top-level widgets excluding menus"""
    return [w for w in QApplication.topLevelWidgets()
            if w.isHidden() and not isinstance(w, QMenu)]

def orphanedWidgets():
    """List of invisible widgets of no parent"""
    return [w for w in QApplication.allWidgets()
            if (not w.parent() and w.isHidden()
                and not isinstance(w, QDesktopWidget))]

def zombieWidgets():
    """List of possibly-deleted widgets but referenced from Python"""
    # weakref.proxy isn't hashable and shouldn't be counted as referenced
    referenced = set(w for w in gc.get_objects()
                     if (isinstance(w, QWidget)
                         and not isinstance(w, weakref.ProxyTypes)))
    return referenced - set(QApplication.allWidgets())

class WidgetsMenuActions(dbgutil.BaseMenuActions):
    """Set up menu to find unused widgets"""

    def _setupMenu(self, menu):
        findtypes = [
            ('&Invisible Windows', invisibleWindows, self.showWidget),
            ('&Orphaned Widgets',  orphanedWidgets,  self.showWidget),
            ('&Zombie Widgets',    zombieWidgets,    self.openGcInfoOfWidget),
            ]
        for name, collect, action in findtypes:
            m = menu.addMenu(name)
            m.menuAction().setStatusTip(collect.__doc__ or '')
            f = WidgetsFinder(m, collect, parent=self)
            f.triggered.connect(action)

        menu.addSeparator()

        a = menu.addAction('&GC Info of Active Window')
        a.triggered.connect(self.openGcInfoOfActiveWindow)
        self._gcInfoDialog = None

    @pyqtSlot(object)
    def showWidget(self, w):
        w.show()
        w.raise_()
        w.activateWindow()

    def _openGcInfoDialog(self):
        if self._gcInfoDialog:
            dlg = self._gcInfoDialog
        else:
            dlg = self._gcInfoDialog = GcInfoDialog()
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()
        return dlg

    @pyqtSlot(object)
    def openGcInfoOfWidget(self, w):
        dlg = self._openGcInfoDialog()
        dlg.update(w)

    @pyqtSlot()
    def openGcInfoOfActiveWindow(self):
        dlg = self._openGcInfoDialog()
        dlg.update(QApplication.activeWindow())

class WidgetsFinder(QObject):
    # not QWidget because C++ part may be deleted
    triggered = pyqtSignal(object)

    def __init__(self, menu, collect, parent=None):
        super(WidgetsFinder, self).__init__(parent)
        self._menu = menu
        self._menu.aboutToShow.connect(self.rebuild)
        self._menu.triggered.connect(self._emitTriggered)
        self._collect = collect
        self._refreshTimer = QTimer(self, interval=100)
        self._refreshTimer.timeout.connect(self.refresh)
        self._menu.aboutToShow.connect(self._refreshTimer.start)
        self._menu.aboutToHide.connect(self._refreshTimer.stop)

    @pyqtSlot()
    def rebuild(self):
        widgets = self._collect()
        self._menu.clear()
        if not widgets:
            self._menu.addAction('(none)').setEnabled(False)
            return
        for i, w in enumerate(sorted(widgets, key=repr)):
            s = re.sub(r'^(tortoisehg\.hgqt|PyQt4\.QtGui)\.', '',
                       repr(w)[1:-1])
            s = s.replace(' object at ', ' at ')
            if i < 10:
                s = '&%d %s' % ((i + 1) % 10, s)
            a = self._menu.addAction(s)
            a.setData(weakref.ref(w))

    @pyqtSlot()
    def refresh(self):
        for a in self._menu.actions():
            wref = a.data()
            if not wref:
                continue
            w = wref()
            a.setEnabled(bool(w))

    @pyqtSlot(QAction)
    def _emitTriggered(self, action):
        wref = action.data()
        w = wref()
        if w:
            self.triggered.emit(w)

class GcInfoDialog(QDialog):

    def __init__(self, parent=None):
        super(GcInfoDialog, self).__init__(parent)
        self.setLayout(QVBoxLayout(self))
        self._infoEdit = QTextBrowser(self)
        self.layout().addWidget(self._infoEdit)
        self._followActiveCheck = QCheckBox('&Follow active window', self)
        self._followActiveCheck.setChecked(True)
        self.layout().addWidget(self._followActiveCheck)

        self._buttonBox = bbox = QDialogButtonBox(self)
        self.layout().addWidget(bbox)
        b = bbox.addButton('&Show Widget', QDialogButtonBox.ActionRole)
        b.clicked.connect(self.showWidget)
        b = bbox.addButton('&Destroy', QDialogButtonBox.ResetRole)
        b.clicked.connect(self.deleteWidget)
        b.setAutoDefault(False)

        self._targetWidgetRef = None
        QApplication.instance().focusChanged.connect(self._updateByFocusChange)
        self._updateButtons()
        self.resize(600, 400)

    def targetWidget(self):
        if not self._targetWidgetRef:
            return
        return self._targetWidgetRef()

    @pyqtSlot()
    def showWidget(self):
        w = self.targetWidget()
        if not w:
            self._updateButtons()
            return
        w.show()
        w.raise_()
        w.activateWindow()

    @pyqtSlot()
    def deleteWidget(self):
        w = self.targetWidget()
        if not w:
            self._updateButtons()
            return
        w.deleteLater()

    @pyqtSlot(QWidget, QWidget)
    def _updateByFocusChange(self, old, now):
        if (not self._followActiveCheck.isChecked()
            or not old or not now or old.window() is now.window()
            or now.window() is self):
            return
        self.update(now.window())

    def update(self, w):
        if not w:
            self._targetWidgetRef = None
            self._updateButtons()
            return
        referrers = gc.get_referrers(w)
        self.setWindowTitle('GC Info - %r' % w)
        self._infoEdit.clear()
        self._infoEdit.append('<h1>Referrers</h1>')
        self._infoEdit.append('<pre>%s</pre>'
                              % qtlib.htmlescape(pprint.pformat(referrers),
                                                 False))
        del referrers
        self._targetWidgetRef = weakref.ref(w)
        self._updateButtons()

    @pyqtSlot()
    def _updateButtons(self):
        self._buttonBox.setEnabled(bool(self.targetWidget()))
