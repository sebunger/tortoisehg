# core.py - top-level menus and hooks
#
# Copyright 2013 Yuya Nishihara <yuya@tcha.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from __future__ import absolute_import

import gc

from tortoisehg.hgqt.qtcore import (
    pyqtSlot,
)
from tortoisehg.hgqt.qtgui import (
    QMainWindow,
)

from tortoisehg.hgqt import run

from . import (
    dbgutil,
    infobar,
    repository,
    widgets,
)

class DebugMenuActions(dbgutil.BaseMenuActions):
    """Set up top-level debug menu"""

    def _setupMenu(self, menu):
        if self._workbench():
            m = menu.addMenu('&InfoBar')
            infobar.InfoBarMenuActions(m, parent=self)
            self._infoBarMenu = m

            m = menu.addMenu('&Repository')
            repository.RepositoryMenuActions(m, parent=self)
            self._repositoryMenu = m

            menu.aboutToShow.connect(self._updateWorkbenchMenus)

        m = menu.addMenu('&Widgets')
        widgets.WidgetsMenuActions(m, parent=self)

        menu.addSeparator()

        a = menu.addAction('Run Full &Garbage Collection')
        a.triggered.connect(self.runGc)

        a = menu.addAction('')  # placeholder to show gc status
        a.setEnabled(False)
        self._gcStatusAction = a

        a = menu.addAction('&Enable Garbage Collector')
        a.setCheckable(True)
        a.triggered.connect(self.setGcEnabled)
        self._gcEnabledAction = a
        menu.aboutToShow.connect(self._updateGcAction)

    @pyqtSlot()
    def _updateWorkbenchMenus(self):
        self._infoBarMenu.setEnabled(bool(self._repoWidget()))
        self._repositoryMenu.setEnabled(bool(self._repoWidget()))

    @pyqtSlot()
    def runGc(self):
        found = gc.collect()
        self._information('GC Result', 'Found %d unreachable objects' % found)

    @property
    def _gcTimer(self):
        return run.qtrun._gc.timer

    def isGcEnabled(self):
        return self._gcTimer.isActive()

    @pyqtSlot(bool)
    def setGcEnabled(self, enabled):
        if enabled:
            self._gcTimer.start()
        else:
            self._gcTimer.stop()

    @pyqtSlot()
    def _updateGcAction(self):
        self._gcStatusAction.setText('  count = %s'
                                     % ', '.join(map(str, gc.get_count())))
        self._gcEnabledAction.setChecked(self.isGcEnabled())

def extsetup(ui):
    class dbgqtrun(run.qtrun.__class__):
        def _createdialog(self, dlgfunc, args, opts):
            dlg, reporoot = super(dbgqtrun, self)._createdialog(dlgfunc, args,
                                                                opts)
            if isinstance(dlg, QMainWindow):
                m = dlg.menuBar().addMenu('&Debug')
                DebugMenuActions(m, parent=dlg)
            return dlg, reporoot

    run.qtrun.__class__ = dbgqtrun
