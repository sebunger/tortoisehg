# dbgutil.py - common functions and classes
#
# Copyright 2013 Yuya Nishihara <yuya@tcha.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from __future__ import absolute_import

from mercurial import (
    pycompat,
)

from tortoisehg.hgqt.qtcore import (
    QObject,
)
from tortoisehg.hgqt.qtgui import (
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QWidget,
)

from tortoisehg.hgqt import workbench

class WidgetNotFound(Exception):
    pass

class BaseMenuActions(QObject):
    """Common helper methods for debug menu actions"""

    def __init__(self, menu, parent=None):
        super(BaseMenuActions, self).__init__(parent)
        self._setupMenu(menu)  # must be implemented by sub class

    def _findParentWidget(self):
        p = self.parent()
        while p:
            if isinstance(p, QWidget):
                return p
            p = p.parent()
        raise WidgetNotFound('no parent widget exists')

    def _parentWidget(self):
        try:
            return self._findParentWidget()
        except WidgetNotFound:
            pass

    def _findWorkbench(self):
        w = self._findParentWidget().window()
        if isinstance(w, workbench.Workbench):
            return w
        raise WidgetNotFound('parent window is not a Workbench')

    def _workbench(self):
        try:
            return self._findWorkbench()
        except WidgetNotFound:
            pass

    def _findRepoWidget(self):
        w = self._findWorkbench().repoTabsWidget.currentWidget()
        if w:
            return w
        raise WidgetNotFound('no RepoWidget is open')

    def _repoWidget(self):
        try:
            return self._findRepoWidget()
        except WidgetNotFound:
            pass

    def _information(self, title, text):
        return QMessageBox.information(self._parentWidget(), title, text)

    def _warning(self, title, text):
        return QMessageBox.warning(self._parentWidget(), title, text)

    def _getText(self, title, label, text=None):
        newtext, ok = QInputDialog.getText(self._parentWidget(), title, label,
                                           QLineEdit.Normal, text or '')
        if ok:
            return pycompat.unicode(newtext)

    def _log(self, msg, label=b'ui.debug'):
        try:
            wb = self._findWorkbench()
            wb.log.output(msg, label=label)
        except WidgetNotFound:
            pass
