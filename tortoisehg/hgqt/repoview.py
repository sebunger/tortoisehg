# Copyright (c) 2009-2010 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
# Copyright 2010 Steve Borho <steve@borho.org>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from mercurial import error

from tortoisehg.util import hglib
from tortoisehg.hgqt.i18n import _
from tortoisehg.hgqt import graph, qtlib, repomodel

from PyQt4.QtCore import *
from PyQt4.QtGui import *

class HgRepoView(QTreeView):

    revisionClicked = pyqtSignal(object)
    revisionAltClicked = pyqtSignal(object)
    revisionSelected = pyqtSignal(object)
    revisionActivated = pyqtSignal(object)
    menuRequested = pyqtSignal(QPoint, object)
    showMessage = pyqtSignal(unicode)
    columnsVisibilityChanged = pyqtSignal()

    def __init__(self, repoagent, cfgname, colselect, parent=None):
        QTreeView.__init__(self, parent)
        self._repoagent = repoagent
        self.current_rev = -1
        self.resized = False
        self.cfgname = cfgname
        self.colselect = colselect

        header = self.header()
        header.setClickable(False)
        header.setMovable(True)
        header.setDefaultAlignment(Qt.AlignLeft)
        header.setHighlightSections(False)
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self.headerMenuRequest)
        header.sectionMoved.connect(self.columnsVisibilityChanged)

        self.createActions()
        self.setItemDelegateForColumn(repomodel.GraphColumn,
                                      GraphDelegate(self))

        self.setAcceptDrops(True)
        if PYQT_VERSION >= 0x40700:
            self.setDefaultDropAction(Qt.MoveAction)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)

        self.setAllColumnsShowFocus(True)
        self.setItemsExpandable(False)
        self.setRootIsDecorated(False)
        self.setUniformRowHeights(True)

        self.setStyle(HgRepoViewStyle(self.style()))
        self._paletteswitcher = qtlib.PaletteSwitcher(self)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.doubleClicked.connect(self.revActivated)
        self.clicked.connect(self.revClicked)

    @property
    def repo(self):
        return self._repoagent.rawRepo()

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            return
        if event.button() == Qt.MidButton:
            self.gotoAncestor(index)
            return
        QTreeView.mousePressEvent(self, event)

    def contextMenuEvent(self, event):
        self.menuRequested.emit(event.globalPos(), self.selectedRevisions())

    def createActions(self):
        menu = QMenu(self)
        act = QAction(_('C&hoose Log Columns...'), self)
        act.triggered.connect(self.setHistoryColumns)
        menu.addAction(act)
        self.headermenu = menu

    @pyqtSlot(QPoint)
    def headerMenuRequest(self, point):
        self.headermenu.exec_(self.header().mapToGlobal(point))

    def setHistoryColumns(self):
        dlg = ColumnSelectDialog(self.colselect[1],
                                 self.model(), self.visibleColumns())
        if dlg.exec_() == QDialog.Accepted:
            self.setVisibleColumns(dlg.selectedColumns())
            self.resizeColumns()
            self._saveColumnSettings()  # for new repository tab

    def _loadColumnSettings(self):
        model = self.model()
        s = QSettings()
        s.beginGroup(self.colselect[0])
        cols = s.value('columns').toStringList()
        cols = [str(col) for col in cols]
        # Fixup older names for columns
        if 'Log' in cols:
            cols[cols.index('Log')] = 'Description'
            s.setValue('columns', cols)
        if 'ID' in cols:
            cols[cols.index('ID')] = 'Rev'
            s.setValue('columns', cols)
        s.endGroup()
        allcolumns = repomodel.ALLCOLUMNS[:model.columnCount()]
        validcols = [col for col in cols if col in allcolumns]
        if not validcols:
            validcols = model._defaultcolumns
        self.setVisibleColumns(validcols)

    def _saveColumnSettings(self):
        s = QSettings()
        s.beginGroup(self.colselect[0])
        s.setValue('columns', self.visibleColumns())
        s.endGroup()

    def visibleColumns(self):
        hh = self.header()
        return [repomodel.ALLCOLUMNS[hh.logicalIndex(visualindex)]
                for visualindex in xrange(hh.count() - hh.hiddenSectionCount())]

    def setVisibleColumns(self, visiblecols):
        if not self.model() or visiblecols == self.visibleColumns():
            return
        hh = self.header()
        hh.sectionMoved.disconnect(self.columnsVisibilityChanged)
        allcolumns = repomodel.ALLCOLUMNS[:self.model().columnCount()]
        for logicalindex, colname in enumerate(allcolumns):
            hh.setSectionHidden(logicalindex, colname not in visiblecols)
        for newvisualindex, colname in enumerate(visiblecols):
            logicalindex = allcolumns.index(colname)
            hh.moveSection(hh.visualIndex(logicalindex), newvisualindex)
        hh.sectionMoved.connect(self.columnsVisibilityChanged)
        self.columnsVisibilityChanged.emit()

    def setModel(self, model):
        oldmodel = self.model()
        QTreeView.setModel(self, model)
        if type(oldmodel) is not type(model):
            # logical columns are vary by model class
            self._loadColumnSettings()
        #Check if the font contains the glyph needed by the model
        if not QFontMetrics(self.font()).inFont(QString(u'\u2605').at(0)):
            model.unicodestar = False
        if not QFontMetrics(self.font()).inFont(QString(u'\u2327').at(0)):
            model.unicodexinabox = False
        self.selectionModel().currentRowChanged.connect(self.onRowChange)
        self._rev_history = []
        self._rev_pos = -1
        self._in_history = False

    def resetBrowseHistory(self, revs, reselrev=None):
        graph = self.model().graph
        self._rev_history = [r for r in revs if r in graph.nodesdict]
        if reselrev is not None and reselrev in self._rev_history:
            self._rev_pos = self._rev_history.index(reselrev)
        else:
            self._rev_pos = -1
        self.forward()

    @pyqtSlot()
    def resizeColumns(self):
        if not self.model():
            return
        hh = self.header()
        hh.setStretchLastSection(False)
        self._resizeColumns()
        hh.setStretchLastSection(True)
        self.resized = True

    def _resizeColumns(self):
        # _resizeColumns misbehaves if called with last section streched
        hh = self.header()
        model = self.model()
        fontm = QFontMetrics(self.font())

        key = '%s/column_widths/%s' % (self.cfgname,
                                       hglib.shortrepoid(self.repo))
        col_widths = [int(w) for w in QSettings().value(key).toStringList()]

        for c in range(model.columnCount()):
            if hh.isSectionHidden(c):
                continue
            if c < len(col_widths) and col_widths[c] > 0:
                w = col_widths[c]
            else:
                w = model.maxWidthValueForColumn(c)

            if isinstance(w, int):
                pass
            elif w is not None:
                w = fontm.width(hglib.tounicode(str(w)) + 'w')
            else:
                w = super(HgRepoView, self).sizeHintForColumn(c)
            self.setColumnWidth(c, w)

    def revFromindex(self, index):
        if not index.isValid():
            return
        model = self.model()
        if model and model.graph:
            row = index.row()
            gnode = model.graph[row]
            return gnode.rev

    def context(self, rev):
        return self.repo.changectx(rev)

    def revClicked(self, index):
        rev = self.revFromindex(index)
        if rev is not None:
            clip = QApplication.clipboard()
            clip.setText(str(self.repo[rev]), QClipboard.Selection)
        if QApplication.keyboardModifiers() & Qt.AltModifier:
            self.revisionAltClicked.emit(rev)
        else:
            self.revisionClicked.emit(rev)

    def revActivated(self, index):
        rev = self.revFromindex(index)
        if rev is not None:
            self.revisionActivated.emit(rev)

    def onRowChange(self, index, index_from):
        rev = self.revFromindex(index)
        if self.current_rev != rev and not self._in_history:
            del self._rev_history[self._rev_pos+1:]
            self._rev_history.append(rev)
            self._rev_pos = len(self._rev_history)-1
        self._in_history = False
        self.current_rev = rev
        self.revisionSelected.emit(rev)

    def selectedRevisions(self):
        """Return the list of selected revisions"""
        selmodel = self.selectionModel()
        return [self.revFromindex(i) for i in selmodel.selectedRows()]

    def gotoAncestor(self, index):
        rev = self.revFromindex(index)
        if rev is None or self.current_rev is None:
            return
        ctx = self.context(self.current_rev)
        ctx2 = self.context(rev)
        if ctx.thgmqunappliedpatch() or ctx2.thgmqunappliedpatch():
            return
        ancestor = ctx.ancestor(ctx2)
        self.showMessage.emit(_("Goto ancestor of %s and %s") % (
                                ctx.rev(), ctx2.rev()))
        self.goto(ancestor.rev())

    def canGoBack(self):
        return bool(self._rev_history and self._rev_pos > 0)

    def canGoForward(self):
        return bool(self._rev_history
                    and self._rev_pos < len(self._rev_history) - 1)

    def back(self):
        if self.canGoBack():
            self._rev_pos -= 1
            idx = self.model().indexFromRev(self._rev_history[self._rev_pos])
            if idx.isValid():
                self._in_history = True
                self.setCurrentIndex(idx)

    def forward(self):
        if self.canGoForward():
            self._rev_pos += 1
            idx = self.model().indexFromRev(self._rev_history[self._rev_pos])
            if idx.isValid():
                self._in_history = True
                self.setCurrentIndex(idx)

    def goto(self, rev):
        """
        Select revision 'rev' (can be anything understood by repo.changectx())
        """
        if isinstance(rev, (unicode, QString)):
            rev = hglib.fromunicode(rev)
        try:
            rev = self.repo.changectx(rev).rev()
        except error.RepoError:
            self.showMessage.emit(_("Can't find revision '%s'")
                                  % hglib.tounicode(str(rev)))
        except LookupError, e:
            self.showMessage.emit(hglib.tounicode(str(e)))
        else:
            idx = self.model().indexFromRev(rev)
            if idx.isValid():
                # avoid unwanted selection change (#1019)
                if self.currentIndex().row() != idx.row():
                    flags = (QItemSelectionModel.ClearAndSelect
                             | QItemSelectionModel.Rows)
                    self.selectionModel().setCurrentIndex(idx, flags)
                self.scrollTo(idx)

    def saveSettings(self, s = None):
        if not s:
            s = QSettings()

        col_widths = []
        for c in range(self.model().columnCount()):
            col_widths.append(self.columnWidth(c))

        try:
            key = '%s/column_widths/%s' % (self.cfgname,
                                           hglib.shortrepoid(self.repo))
            s.setValue(key, col_widths)
        except EnvironmentError:
            pass

        self._saveColumnSettings()

    def resizeEvent(self, e):
        # re-size columns the smart way: the column holding Description
        # is re-sized according to the total widget size.
        if self.resized and e.oldSize().width() != e.size().width():
            model = self.model()
            total_width = stretch_col = 0

            for c in range(model.columnCount()):
                if c == repomodel.DescColumn:
                    #save the description column
                    stretch_col = c
                else:
                    #total the other widths
                    total_width += self.columnWidth(c)

            width = max(self.viewport().width() - total_width, 100)
            self.setColumnWidth(stretch_col, width)

        super(HgRepoView, self).resizeEvent(e)

    def enablefilterpalette(self, enable):
        self._paletteswitcher.enablefilterpalette(enable)

class HgRepoViewStyle(QStyle):
    "Override a style's drawPrimitive method to customize the drop indicator"
    def __init__(self, style):
        style.__class__.__init__(self)
        self._style = style
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PE_IndicatorItemViewItemDrop:
            # Drop indicators should be painted using the full viewport width
            if option.rect.height() != 0:
                vp = widget.viewport().rect()
                painter.drawRect(vp.x(), option.rect.y(),
                                 vp.width() - 1, 0.5)
        else:
            self._style.drawPrimitive(element, option, painter, widget)
    # Delegate all other methods overridden by QProxyStyle to the base class
    def drawComplexControl(self, *args):
        return self._style.drawComplexControl(*args)
    def drawControl(self, *args):
        return self._style.drawControl(*args)
    def drawItemPixmap(self, *args):
        return self._style.drawItemPixmap(*args)
    def drawItemText(self, *args):
        return self._style.drawItemText(*args)
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


def get_style(line_type, active):
    if line_type == graph.LINE_TYPE_GRAFT:
        return Qt.DashLine
    if line_type == graph.LINE_TYPE_OBSOLETE:
        return Qt.DotLine
    return Qt.SolidLine

def get_width(line_type, active):
    if line_type >= graph.LINE_TYPE_FAMILY or not active:
        return 1
    return 2

def _edge_color(edge, active):
    if not active or edge.linktype == graph.LINE_TYPE_FAMILY:
        return "gray"
    else:
        return repomodel.get_color(edge.color)


class GraphDelegate(QStyledItemDelegate):

    def __init__(self, parent):
        super(GraphDelegate, self).__init__(parent)
        assert isinstance(parent, QWidget)
        # assumes 4px as text and decoration margins of other columns
        fm = parent.fontMetrics()
        self._rowheight = self._rowheighthint = max(fm.height() + 4, 16)

    def _col2x(self, col):
        maxradius = max(self._rowheight / 2, 1)
        return maxradius * (col + 1)

    def _colcount(self, width):
        maxradius = max(self._rowheight / 2, 1)
        return (width + maxradius - 1) // maxradius

    def _dotradius(self):
        return 0.4 * self._rowheight

    def paint(self, painter, option, index):
        QStyledItemDelegate.paint(self, painter, option, index)
        # update to the actual height that should be the same for all rows
        self._rowheight = option.rect.height()
        visibleend = self._colcount(option.rect.width())
        gnode = index.data(repomodel.GraphNodeRole).toPyObject()
        painter.save()
        try:
            painter.setClipRect(option.rect)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.translate(option.rect.topLeft())
            self._drawEdges(painter, index, gnode, visibleend)
            if gnode.x < visibleend:
                self._drawNode(painter, index, gnode)
        finally:
            painter.restore()

    def _drawEdges(self, painter, index, gnode, visibleend):
        h = self._rowheight
        dot_y = h / 2

        def isactive(e):
            m = index.model()
            return m.isActiveRev(e.startrev) and m.isActiveRev(e.endrev)
        def lineimportance(pe):
            return isactive(pe[1]), pe[1].importance

        for y1, y4, lines in ((dot_y, dot_y + h, gnode.bottomlines),
                              (dot_y - h, dot_y, gnode.toplines)):
            y2 = y1 + 1 * (y4 - y1)/4
            ymid = (y1 + y4)/2
            y3 = y1 + 3 * (y4 - y1)/4

            # omit invisible lines
            lines = [((start, end), e) for (start, end), e in lines
                     if start < visibleend or end < visibleend]
            # remove hidden lines that can be partly visible due to antialiasing
            lines = dict(sorted(lines, key=lineimportance)).items()
            # still necessary to sort by importance because lines can partially
            # overlap near contact point
            lines.sort(key=lineimportance)

            for (start, end), e in lines:
                active = isactive(e)
                lpen = QPen(QColor(_edge_color(e, active)))
                lpen.setStyle(get_style(e.linktype, active))
                lpen.setWidth(get_width(e.linktype, active))
                painter.setPen(lpen)
                x1 = self._col2x(start)
                x2 = self._col2x(end)
                if x1 == x2:
                    painter.drawLine(x1, y1, x2, y4)
                else:
                    path = QPainterPath()
                    path.moveTo(x1, y1)
                    path.cubicTo(x1, y2,
                                 x1, y2,
                                 (x1 + x2) / 2, ymid)
                    path.cubicTo(x2, y3,
                                 x2, y3,
                                 x2, y4)
                    painter.drawPath(path)

    def _drawNode(self, painter, index, gnode):
        m = index.model()
        if not m.isActiveRev(gnode.rev):
            dot_color = QColor("gray")
            radius = self._dotradius() * 0.8
        else:
            dot_color = QBrush(index.data(Qt.ForegroundRole)).color()
            radius = self._dotradius()
        dotcolor = dot_color.lighter()
        pencolor = dot_color.darker()
        truewhite = QColor("white")
        white = QColor("white")
        fillcolor = gnode.rev is None and white or dotcolor

        pen = QPen(pencolor)
        pen.setWidthF(1.5)
        painter.setPen(pen)

        centre_x = self._col2x(gnode.x)
        centre_y = self._rowheight / 2

        def circle(r):
            rect = QRectF(centre_x - r,
                          centre_y - r,
                          2 * r, 2 * r)
            painter.drawEllipse(rect)

        def closesymbol(s):
            rect_ = QRectF(centre_x - 1.5 * s, centre_y - 0.5 * s, 3 * s, s)
            painter.drawRect(rect_)

        def diamond(r):
            poly = QPolygonF([QPointF(centre_x - r, centre_y),
                              QPointF(centre_x, centre_y - r),
                              QPointF(centre_x + r, centre_y),
                              QPointF(centre_x, centre_y + r),
                              QPointF(centre_x - r, centre_y),])
            painter.drawPolygon(poly)

        hiddenrev = gnode.hidden
        if hiddenrev:
            painter.setBrush(truewhite)
            white.setAlpha(64)
            fillcolor.setAlpha(64)
        if gnode.shape == graph.NODE_SHAPE_APPLIEDPATCH:
            # diamonds for patches
            symbolsize = radius / 1.5
            if hiddenrev:
                diamond(symbolsize)
            if gnode.wdparent:
                painter.setBrush(white)
                diamond(2 * 0.9 * symbolsize)
            painter.setBrush(fillcolor)
            diamond(symbolsize)
        elif gnode.shape == graph.NODE_SHAPE_UNAPPLIEDPATCH:
            symbolsize = radius / 1.5
            if hiddenrev:
                diamond(symbolsize)
            patchcolor = QColor('#dddddd')
            painter.setBrush(patchcolor)
            painter.setPen(patchcolor)
            diamond(symbolsize)
        elif gnode.shape == graph.NODE_SHAPE_CLOSEDBRANCH:
            symbolsize = 0.5 * radius
            if hiddenrev:
                closesymbol(symbolsize)
            painter.setBrush(fillcolor)
            closesymbol(symbolsize)
        else:  # circles for normal revisions
            symbolsize = 0.5 * radius
            if hiddenrev:
                circle(symbolsize)
            if gnode.wdparent:
                painter.setBrush(white)
                circle(0.9 * radius)
            painter.setBrush(fillcolor)
            circle(symbolsize)

    def sizeHint(self, option, index):
        gnode = index.data(repomodel.GraphNodeRole).toPyObject()
        if gnode:
            # return width for current height assuming that row height
            # is calculated first (mimic width-for-height policy)
            return QSize(self._col2x(gnode.cols), self._rowheighthint)
        else:
            return QSize(0, 0)


class ColumnSelectDialog(QDialog):
    def __init__(self, name, model, curcolumns, parent=None):
        QDialog.__init__(self, parent)
        all = repomodel.ALLCOLUMNS[:model.columnCount()]
        colnames = dict(repomodel.COLUMNHEADERS)

        self.setWindowTitle(name)
        self.setWindowFlags(self.windowFlags() & \
                            ~Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(250, 265)

        disabled = [c for c in all if c not in curcolumns]

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

        list = QListWidget()
        # enabled cols are listed in sorted order, disabled are listed last
        for c in curcolumns + disabled:
            item = QListWidgetItem(colnames[c])
            item.columnid = c
            item.setFlags(Qt.ItemIsSelectable |
                          Qt.ItemIsEnabled |
                          Qt.ItemIsDragEnabled |
                          Qt.ItemIsUserCheckable)
            if c in curcolumns:
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            list.addItem(item)
        list.setDragDropMode(QListView.InternalMove)
        layout.addWidget(list)
        self.list = list

        layout.addWidget(QLabel(_('Drag to change order')))

        # dialog buttons
        BB = QDialogButtonBox
        bb = QDialogButtonBox(BB.Ok|BB.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def selectedColumns(self):
        cols = []
        for i in xrange(self.list.count()):
            item = self.list.item(i)
            if item.checkState() == Qt.Checked:
                cols.append(item.columnid)
        return cols
