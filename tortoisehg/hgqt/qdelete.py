# qdelete.py - QDelete dialog for TortoiseHg
#
# Copyright 2010 Steve Borho <steve@borho.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from tortoisehg.util import hglib
from tortoisehg.hgqt import qtlib
from tortoisehg.hgqt.i18n import _

class QDeleteDialog(QDialog):

    def __init__(self, patches, parent):
        super(QDeleteDialog, self).__init__(parent)
        self.setWindowTitle(_('Delete Patches'))
        self.setWindowIcon(qtlib.geticon('hg-qdelete'))
        self.setWindowFlags(self.windowFlags()
                            & ~Qt.WindowContextHelpButtonHint)

        self.setLayout(QVBoxLayout())

        msg = _('Remove patches from queue?')
        patchesu = u'<li>'.join(patches)
        lbl = QLabel(u'<b>%s<ul><li>%s</ul></b>' % (msg, patchesu))
        self.layout().addWidget(lbl)

        self._keepchk = QCheckBox(_('Keep patch files'))
        self._keepchk.setChecked(True)
        self.layout().addWidget(self._keepchk)

        BB = QDialogButtonBox
        bbox = QDialogButtonBox(BB.Ok|BB.Cancel)
        bbox.accepted.connect(self.accept)
        bbox.rejected.connect(self.reject)
        self.layout().addWidget(bbox)

    def options(self):
        return {'keep': self._keepchk.isChecked()}
