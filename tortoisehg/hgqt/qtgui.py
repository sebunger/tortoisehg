# qtgui.py - PyQt4/5 compatibility wrapper
#
# Copyright 2015 Yuya Nishihara <yuya@tcha.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Thin compatibility wrapper for QtGui and QtWidgets of Qt5"""

from __future__ import absolute_import

from .qtcore import QT_API

if QT_API == 'PyQt4':
    # http://pyqt.sourceforge.net/Docs/PyQt5/pyqt4_differences.html
    from PyQt4.QtGui import *  # pytype: disable=import-error
    from PyQt4.QtGui import QFileDialog as _QFileDialog  # pytype: disable=import-error
    class QFileDialog(_QFileDialog):
        getOpenFileName = _QFileDialog.getOpenFileNameAndFilter
        getOpenFileNames = _QFileDialog.getOpenFileNamesAndFilter
        getSaveFileName = _QFileDialog.getSaveFileNameAndFilter
    class QProxyStyle(QStyle):
        def __init__(self, style=None):
            if style is None:
                style = QApplication.style()
            style.__class__.__init__(self)
            self._style = style
        # Delegate all methods overridden by QProxyStyle to the base class
        def drawComplexControl(self, *args):
            return self._style.drawComplexControl(*args)
        def drawControl(self, *args):
            return self._style.drawControl(*args)
        def drawItemPixmap(self, *args):
            return self._style.drawItemPixmap(*args)
        def drawItemText(self, *args):
            return self._style.drawItemText(*args)
        def drawPrimitive(self, *args):
            return self._style.drawPrimitive(*args)
        def generatedIconPixmap(self, *args):
            return self._style.generatedIconPixmap(*args)
        def hitTestComplexControl(self, *args):
            return self._style.hitTestComplexControl(*args)
        def itemPixmapRect(self, *args):
            return self._style.itemPixmapRect(*args)
        def itemTextRect(self, *args):
            return self._style.itemTextRect(*args)
        def pixelMetric(self, *args):
            return self._style.pixelMetric(*args)
        def polish(self, *args):
            return self._style.polish(*args)
        def sizeFromContents(self, *args):
            return self._style.sizeFromContents(*args)
        def standardPalette(self):
            return self._style.standardPalette()
        def standardPixmap(self, *args):
            return self._style.standardPixmap(*args)
        def styleHint(self, *args):
            return self._style.styleHint(*args)
        def subControlRect(self, *args):
            return self._style.subControlRect(*args)
        def subElementRect(self, *args):
            return self._style.subElementRect(*args)
        def unpolish(self, *args):
            return self._style.unpolish(*args)
        def event(self, *args):
            return self._style.event(*args)
        def layoutSpacingImplementation(self, *args):
            return self._style.layoutSpacingImplementation(*args)
        def standardIconImplementation(self, *args):
            return self._style.standardIconImplementation(*args)
elif QT_API == 'PyQt5':
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    QStyleOptionViewItemV2 = QStyleOptionViewItem
    QStyleOptionViewItemV3 = QStyleOptionViewItem
    QStyleOptionViewItemV4 = QStyleOptionViewItem
else:
    raise RuntimeError('unsupported Qt API: %s' % QT_API)
