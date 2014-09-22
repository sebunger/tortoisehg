# Copyright (c) 2009-2010 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
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

import binascii, os, re

from mercurial import util, error

from tortoisehg.util import hglib
from tortoisehg.hgqt import filedata, graph, qtlib

from tortoisehg.hgqt.i18n import _

from PyQt4.QtCore import *
from PyQt4.QtGui import *

nullvariant = QVariant()

mqpatchmimetype = 'application/thg-mqunappliedpatch'

# TODO: Remove these two when we adopt GTK author color scheme
COLORS = [ "blue", "darkgreen", "red", "green", "darkblue", "purple",
           "dodgerblue", Qt.darkYellow, "magenta", "darkred", "darkmagenta",
           "darkcyan", ]
COLORS = [str(QColor(x).name()) for x in COLORS]

# pick names from "hg help templating" if any
GraphColumn = 0
RevColumn = 1
BranchColumn = 2
DescColumn = 3
AuthorColumn = 4
TagsColumn = 5
LatestTagColumn = 6
NodeColumn = 7
AgeColumn = 8
LocalDateColumn = 9
UtcDateColumn = 10
ChangesColumn = 11
ConvertedColumn = 12
PhaseColumn = 13
FileColumn = 14

COLUMNHEADERS = (
    ('Graph', _('Graph', 'column header')),
    ('Rev', _('Rev', 'column header')),
    ('Branch', _('Branch', 'column header')),
    ('Description', _('Description', 'column header')),
    ('Author', _('Author', 'column header')),
    ('Tags', _('Tags', 'column header')),
    ('Latest tags', _('Latest tags', 'column header')),
    ('Node', _('Node', 'column header')),
    ('Age', _('Age', 'column header')),
    ('LocalTime', _('Local Time', 'column header')),
    ('UTCTime', _('UTC Time', 'column header')),
    ('Changes', _('Changes', 'column header')),
    ('Converted', _('Converted From', 'column header')),
    ('Phase', _('Phase', 'column header')),
    ('Filename', _('Filename', 'column header')),
    )
ALLCOLUMNS = tuple(name for name, _text in COLUMNHEADERS)

UNAPPLIED_PATCH_COLOR = '#999999'
HIDDENREV_COLOR = '#666666'

GraphNodeRole = Qt.UserRole + 0

def get_color(n, ignore=()):
    """
    Return a color at index 'n' rotating in the available
    colors. 'ignore' is a list of colors not to be chosen.
    """
    ignore = [str(QColor(x).name()) for x in ignore]
    colors = [x for x in COLORS if x not in ignore]
    if not colors: # ghh, no more available colors...
        colors = COLORS
    return colors[n % len(colors)]

def _parsebranchcolors(value):
    r"""Parse tortoisehg.branchcolors setting

    >>> _parsebranchcolors('foo:#123456  bar:#789abc ')
    [('foo', '#123456'), ('bar', '#789abc')]
    >>> _parsebranchcolors(r'foo\ bar:black foo\:bar:white')
    [('foo bar', 'black'), ('foo:bar', 'white')]

    >>> _parsebranchcolors(r'\u00c0:black')
    [('\xc0', 'black')]
    >>> _parsebranchcolors('\xc0:black')
    [('\xc0', 'black')]

    >>> _parsebranchcolors(None)
    []
    >>> _parsebranchcolors('ill:formed:value no-value')
    []
    >>> _parsebranchcolors(r'\ubad:unicode-repr')
    []
    """
    if not value:
        return []

    colors = []
    for e in re.split(r'(?:(?<=\\\\)|(?<!\\)) ', value):
        pair = re.split(r'(?:(?<=\\\\)|(?<!\\)):', e)
        if len(pair) != 2:
            continue # ignore ill-formed
        key, val = pair
        key = key.replace('\\:', ':').replace('\\ ', ' ')
        if r'\u' in key:
            # apply unicode_escape only if \u found, so that raw non-ascii
            # value isn't always mangled.
            try:
                key = hglib.fromunicode(key.decode('unicode_escape'))
            except (UnicodeDecodeError, UnicodeEncodeError):
                continue
        colors.append((key, val))
    return colors

def _renderlabels(labels, margin=2):
    if not labels:
        return
    font = QApplication.font('QAbstractItemView')
    fm = QFontMetrics(font, None)  # screen-compatible (i.e. QPixmap) metrics
    twidths = [fm.width(t) for t, _s in labels]
    th = fm.height()

    padw = 2
    padh = 1  # may overwrite horizontal frame to fit row

    pix = QPixmap(sum(twidths) + len(labels) * (2 * padw + margin) - margin,
                  th + 2 * padh)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setFont(font)
    x = 0
    for (text, style), tw in zip(labels, twidths):
        lw = tw + 2 * padw
        lh = th + 2 * padh
        # draw bevel, background and text in order
        bg = qtlib.getbgcoloreffect(style)
        painter.fillRect(x, 0, lw, lh, bg.darker(110))
        painter.fillRect(x + 1, 1, lw - 2, lh - 2, bg.lighter(110))
        painter.fillRect(x + 2, 2, lw - 4, lh - 4, bg)
        painter.setPen(qtlib.gettextcoloreffect(style))
        painter.drawText(x + padw, padh, tw, th, 0, text)
        x += lw + margin
    painter.end()
    return pix


class HgRepoListModel(QAbstractTableModel):
    """
    Model used for displaying the revisions of a Hg *local* repository
    """
    showMessage = pyqtSignal(unicode)
    filled = pyqtSignal()
    loaded = pyqtSignal()

    _defaultcolumns = ('Graph', 'Rev', 'Branch', 'Description', 'Author',
                       'Age', 'Tags', 'Phase')

    _mqtags = ('qbase', 'qtip', 'qparent')

    def __init__(self, repo, branch, revset, rfilter, parent,
                 allparents=False, showgraftsource=True):
        """
        repo is a hg repo instance
        """
        QAbstractTableModel.__init__(self, parent)
        self._cache = []
        self.graph = None
        self.timerHandle = None
        self.rowcount = 0
        self.repo = repo
        self.revset = frozenset(revset)
        self.filterbyrevset = rfilter
        self.unicodestar = True
        self.unicodexinabox = True
        self.latesttags = {-1: 'null'}
        self.fullauthorname = False
        self.filterbranch = branch  # unicode
        self.allparents = allparents
        self.showgraftsource = showgraftsource

        # To be deleted
        self._user_colors = {}
        self._branch_colors = {}

        if repo:
            self.initBranchColors()
            self.reloadConfig()
            self._initGraph()

    def initBranchColors(self):
        # Set all the branch colors once on a fixed order,
        # which should make the branch colors more stable

        # Always assign the first color to the default branch
        self.namedbranch_color('default')

        # Set the colors specified in the tortoisehg.brachcolors config key
        self._branch_colors.update(_parsebranchcolors(
            self.repo.ui.config('tortoisehg', 'branchcolors')))

        # Then assign colors to all branches in alphabetical order
        # Note that re-assigning the color to the default branch
        # is not expensive
        for branch in sorted(self.repo.branchmap()):
            self.namedbranch_color(branch)

    def setBranch(self, branch, allparents=False):
        self.filterbranch = branch
        self.allparents = allparents
        self._initGraph()

    def setShowGraftSource(self, visible):
        self.showgraftsource = visible
        self._initGraph()

    def _initGraph(self):
        self.invalidateCache()
        opts = {
            'branch': hglib.fromunicode(self.filterbranch),
            'showgraftsource': self.showgraftsource,
            }
        if self.revset and self.filterbyrevset:
            opts['revset'] = self.revset
            opts['showfamilyline'] = \
                self.repo.ui.configbool('tortoisehg', 'showfamilyline', True)
            grapher = graph.revision_grapher(self.repo, opts)
            self.graph = graph.Graph(self.repo, grapher, include_mq=False)
        else:
            opts['allparents'] = self.allparents
            grapher = graph.revision_grapher(self.repo, opts)
            self.graph = graph.Graph(self.repo, grapher, include_mq=True)
        self.rowcount = 0
        self.layoutChanged.emit()
        self.showMessage.emit('')
        QTimer.singleShot(0, self, SIGNAL('filled()'))

    def setRevset(self, revset):
        self.revset = frozenset(revset)
        self.invalidateCache()

    def reloadConfig(self):
        _ui = self.repo.ui
        self.fill_step = int(_ui.config('tortoisehg', 'graphlimit', 500))
        self.authorcolor = _ui.configbool('tortoisehg', 'authorcolor')
        self.fullauthorname = _ui.configbool('tortoisehg', 'fullauthorname')

    def invalidate(self):
        self.reloadConfig()
        self.invalidateCache()
        self.layoutChanged.emit()

    def branch(self):
        return self.filterbranch

    def canFetchMore(self, parent):
        if parent.isValid():
            return False
        return not self.graph.isfilled()

    def fetchMore(self, parent):
        if parent.isValid() or self.graph.isfilled():
            return
        self.graph.build_nodes(self.fill_step)
        self.updateRowCount()

    def ensureBuilt(self, rev):
        """
        Make sure rev data is available (graph element created).

        """
        if (self.graph.isfilled()
            # working rev must exist once build_nodes() is invoked
            or (len(self.graph) > 0 and rev is None)
            or (len(self.graph) > 0 and self.graph[-1].rev <= rev)):
            return
        self.graph.build_nodes(self.fill_step / 2, rev)
        self.updateRowCount()

    def loadall(self):
        self.timerHandle = self.startTimer(1)

    def timerEvent(self, event):
        if event.timerId() == self.timerHandle:
            self.showMessage.emit(_('filling (%d)')%(len(self.graph)))
            if self.graph.isfilled():
                self.killTimer(self.timerHandle)
                self.timerHandle = None
                self.showMessage.emit('')
                self.loaded.emit()
            # we only fill the graph data structures without telling
            # views until the model is loaded, to keep maximal GUI
            # reactivity
            elif not self.graph.build_nodes():
                self.killTimer(self.timerHandle)
                self.timerHandle = None
                self.updateRowCount()
                self.showMessage.emit('')
                self.loaded.emit()

    def updateRowCount(self):
        currentlen = self.rowcount
        newlen = len(self.graph)

        if newlen > self.rowcount:
            self.beginInsertRows(QModelIndex(), currentlen, newlen-1)
            self.rowcount = newlen
            self.endInsertRows()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return self.rowcount

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(ALLCOLUMNS) - 1  # no FileColumn

    def maxWidthValueForColumn(self, column):
        if self.graph is None:
            return 'XXXX'
        if column == RevColumn:
            return '8' * len(str(len(self.repo))) + '+'
        if column == NodeColumn:
            return '8' * 12 + '+'
        if column in (LocalDateColumn, UtcDateColumn):
            return hglib.displaytime(util.makedate())
        if column in (TagsColumn, LatestTagColumn):
            try:
                return sorted(self.repo.tags().keys(), key=lambda x: len(x))[-1][:10]
            except IndexError:
                pass
        if column == BranchColumn:
            try:
                return sorted(self.repo.branchmap(), key=lambda x: len(x))[-1]
            except IndexError:
                pass
        if column == FileColumn:
            return self.filename
        if column == ChangesColumn:
            return 'Changes'
        # Fall through for DescColumn
        return None

    def user_color(self, user):
        'deprecated, please replace with hgtk color scheme'
        if user not in self._user_colors:
            self._user_colors[user] = get_color(len(self._user_colors),
                                                self._user_colors.values())
        return self._user_colors[user]

    def namedbranch_color(self, branch):
        'deprecated, please replace with hgtk color scheme'
        if branch not in self._branch_colors:
            self._branch_colors[branch] = get_color(len(self._branch_colors))
        return self._branch_colors[branch]

    def invalidateCache(self):
        self._cache = []

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return nullvariant
        gnode = self.graph[index.row()]
        if role == Qt.DisplayRole:
            if index.column() == FileColumn:
                return hglib.tounicode(gnode.extra[0])
        if role == Qt.FontRole:
            if index.column() in (NodeColumn, ConvertedColumn):
                return QFont("Monospace")
            if index.column() == DescColumn and gnode.wdparent:
                font = QApplication.font('QAbstractItemView')
                font.setBold(True)
                return font
        if role == Qt.ForegroundRole:
            if (gnode.shape == graph.NODE_SHAPE_UNAPPLIEDPATCH
                and index.column() != DescColumn):
                return QColor(UNAPPLIED_PATCH_COLOR)
            if gnode.hidden and index.column() != GraphColumn:
                return QColor(HIDDENREV_COLOR)
        if role == GraphNodeRole:
            return gnode
        if (role, index.column()) not in self._cacheindexmap:
            return nullvariant
        # repo may be changed while reading in case of postpull=rebase for
        # example, and result in RevlogError. (issue #429)
        try:
            return self.safedata(index, role)
        except error.RevlogError, e:
            if 'THGDEBUG' in os.environ:
                raise
            if role == Qt.DisplayRole:
                return QVariant(hglib.tounicode(str(e)))
            else:
                return nullvariant

    def safedata(self, index, role):
        row = index.row()
        graphlen = len(self.graph)
        cachelen = len(self._cache)
        if graphlen > cachelen:
            self._cache.extend([None] * len(self._cacheindexmap)
                               for _i in xrange(graphlen - cachelen))
        data = self._cache[row]
        idx = self._cacheindexmap[role, index.column()]
        if data[idx] is None:
            try:
                result = self.rawdata(index, role)
            except util.Abort:
                result = nullvariant
            data[idx] = result
        return data[idx]

    def rawdata(self, index, role):
        row = index.row()
        column = index.column()
        gnode = self.graph[row]
        ctx = self.repo.changectx(gnode.rev)

        if role == Qt.DisplayRole:
            text = self._columnmap[column](self, ctx)
            if not isinstance(text, (QString, unicode)):
                text = hglib.tounicode(text)
            return QVariant(text)
        elif role == Qt.ForegroundRole:
            if column == AuthorColumn:
                if self.authorcolor:
                    return QVariant(QColor(self.user_color(ctx.user())))
                return nullvariant
            if column in (GraphColumn, BranchColumn):
                return QVariant(QColor(self.namedbranch_color(ctx.branch())))
        elif role == Qt.DecorationRole and column == DescColumn:
            return QVariant(self._renderrevlabels(ctx))
        elif role == Qt.DecorationRole and column == ChangesColumn:
            return QVariant(self._renderchanges(ctx))
        return nullvariant

    def flags(self, index):
        flags = super(HgRepoListModel, self).flags(index)
        if not index.isValid():
            return flags
        row = index.row()
        if row >= len(self.graph) and not self.repo.ui.debugflag:
            # TODO: should not happen; internal data went wrong (issue #754)
            return Qt.NoItemFlags
        gnode = self.graph[row]
        if not self.isActiveRev(gnode.rev):
            return Qt.NoItemFlags
        if gnode.shape == graph.NODE_SHAPE_UNAPPLIEDPATCH:
            flags |= Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        if gnode.rev is None:
            flags |= Qt.ItemIsDropEnabled
        return flags

    def isActiveRev(self, rev):
        """True if the specified rev is not excluded by revset"""
        return not self.revset or rev in self.revset

    def mimeTypes(self):
        return QStringList([mqpatchmimetype])

    def supportedDropActions(self):
        return Qt.MoveAction

    def mimeData(self, indexes):
        data = set()
        for index in indexes:
            row = str(index.row())
            if row not in data:
                data.add(row)
        qmd = QMimeData()
        bytearray = QByteArray(','.join(sorted(data, reverse=True)))
        qmd.setData(mqpatchmimetype, bytearray)
        return qmd

    def dropMimeData(self, data, action, row, column, parent):
        if mqpatchmimetype not in data.formats():
            return False
        dragrows = [int(r) for r in str(data.data(mqpatchmimetype)).split(',')]
        destrow = parent.row()
        if destrow < 0:
            return False
        unapplied = self.repo.thgmqunappliedpatches[::-1]
        applied = [p.name for p in self.repo.mq.applied[::-1]]
        if max(dragrows) >= len(unapplied):
            return False
        dragpatches = [unapplied[d] for d in dragrows]
        allpatches = unapplied + applied
        if destrow < len(allpatches):
            destpatch = allpatches[destrow]
        else:
            destpatch = None  # next to working rev

        hglib.movemqpatches(self.repo, destpatch, dragpatches)
        repoagent = self.repo._pyqtobj  # TODO
        repoagent.pollStatus()
        return True

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return COLUMNHEADERS[section][1]

    def indexFromRev(self, rev):
        if self.graph is None:
            return QModelIndex()
        self.ensureBuilt(rev)
        row = self.graph.index(rev)
        if row >= 0:
            return self.index(row, 0)
        return QModelIndex()

    def getbranch(self, ctx):
        b = hglib.tounicode(ctx.branch())
        if ctx.extra().get('close'):
            if self.unicodexinabox:
                b += u' \u2327'
            else:
                b += u'--'
        return b

    def getlatesttags(self, ctx):
        rev = ctx.rev()
        todo = [rev]
        repo = self.repo
        while todo:
            rev = todo.pop()
            if rev in self.latesttags:
                continue
            ctx = repo[rev]
            tags = [t for t in ctx.tags()
                    if repo.tagtype(t) and repo.tagtype(t) != 'local']
            if tags:
                self.latesttags[rev] = ':'.join(sorted(tags))
                continue
            try:
                if (ctx.parents()):
                    ptag = max(
                        self.latesttags[p.rev()] for p in ctx.parents())
                else:
                    ptag = ""
            except KeyError:
                # Cache miss - recurse
                todo.append(rev)
                todo.extend(p.rev() for p in ctx.parents())
                continue
            self.latesttags[rev] = ptag
        return self.latesttags[rev]

    def gettags(self, ctx):
        if ctx.rev() is None:
            return ''
        tags = [t for t in ctx.tags() if t not in self._mqtags]
        return hglib.tounicode(','.join(tags))

    def getrev(self, ctx):
        rev = ctx.rev()
        if type(rev) is int:
            return str(rev)
        elif rev is None:
            return u'%d+' % ctx.p1().rev()
        else:
            return ''

    def getauthor(self, ctx):
        try:
            user = ctx.user()
            if not self.fullauthorname:
                user = hglib.username(user)
            return user
        except error.Abort:
            return _('Mercurial User')

    def getlog(self, ctx):
        if ctx.rev() is None:
            if self.unicodestar:
                # The Unicode symbol is a black star:
                return u'\u2605 ' + _('Working Directory') + u' \u2605'
            else:
                return '*** ' + _('Working Directory') + ' ***'
        if self.repo.ui.configbool('tortoisehg', 'longsummary'):
            limit = 0x7fffffff  # unlimited (elide it by view)
        else:
            limit = None  # first line
        return hglib.longsummary(ctx.description(), limit)

    def _renderrevlabels(self, ctx):
        labels = []
        if ctx.rev() is None:
            for pctx in ctx.parents():
                branchheads = hglib.branchheads(self.repo)
                if branchheads and pctx.node() not in branchheads:
                    labels.append((_('Not a head revision!'), 'log.warning'))
            return _renderlabels(labels)

        if ctx.thgbranchhead():
            labels.append((hglib.tounicode(ctx.branch()), 'log.branch'))

        if ctx.thgmqunappliedpatch():
            style = 'log.unapplied_patch'
            labels.append((hglib.tounicode(ctx._patchname), style))

        for mark in ctx.bookmarks():
            style = 'log.bookmark'
            if mark == self.repo._bookmarkcurrent:
                bn = self.repo._bookmarks[self.repo._bookmarkcurrent]
                if bn in self.repo.dirstate.parents():
                    style = 'log.curbookmark'
            labels.append((hglib.tounicode(mark), style))

        for tag in ctx.thgtags():
            if self.repo.thgmqtag(tag):
                style = 'log.patch'
            else:
                style = 'log.tag'
            labels.append((hglib.tounicode(tag), style))

        return _renderlabels(labels)

    def _renderchanges(self, ctx):
        """Return the MAR status for the given ctx."""
        labels = []
        M, A, R = ctx.changesToParent(0)
        if A:
            labels.append((str(len(A)), 'log.added'))
        if M:
            labels.append((str(len(M)), 'log.modified'))
        if R:
            labels.append((str(len(R)), 'log.removed'))
        return _renderlabels(labels, margin=0)

    def getconv(self, ctx):
        if ctx.rev() is not None:
            extra = ctx.extra()
            cvt = extra.get('convert_revision', '')
            if cvt:
                if cvt.startswith('svn:'):
                    return cvt.split('@')[-1]
                if len(cvt) == 40:
                    try:
                        binascii.unhexlify(cvt)
                        return cvt[:12]
                    except TypeError:
                        pass
            cvt = extra.get('p4', '')
            if cvt:
                return cvt
        return ''

    def getphase(self, ctx):
        if ctx.rev() is None:
            return ''
        try:
            return ctx.phasestr()
        except:
            return 'draft'

    _columnmap = {
        RevColumn: getrev,
        BranchColumn: getbranch,
        DescColumn: getlog,
        AuthorColumn: getauthor,
        TagsColumn: gettags,
        LatestTagColumn: getlatesttags,
        NodeColumn: lambda self, ctx: str(ctx),
        AgeColumn: lambda self, ctx: hglib.age(ctx.date()).decode('utf-8'),
        LocalDateColumn: lambda self, ctx: hglib.displaytime(ctx.date()),
        UtcDateColumn: lambda self, ctx: hglib.utctime(ctx.date()),
        ConvertedColumn: getconv,
        PhaseColumn: getphase,
        }

    # (role, column): index in _cache[row]
    _cacheindexmap = dict((k, i) for i, k in enumerate(
        [(Qt.DisplayRole, c) for c in _columnmap]
        + [(Qt.ForegroundRole, GraphColumn),
           (Qt.ForegroundRole, BranchColumn),
           (Qt.ForegroundRole, AuthorColumn),
           (Qt.DecorationRole, DescColumn),
           (Qt.DecorationRole, ChangesColumn)]))


class FileRevModel(HgRepoListModel):
    """
    Model used to manage the list of revisions of a file, in file
    viewer of in diff-file viewer dialogs.
    """

    _defaultcolumns = ('Graph', 'Rev', 'Branch', 'Description', 'Author',
                       'Age', 'Filename')

    def __init__(self, repo, filename, parent=None):
        """
        data is a HgHLRepo instance
        """
        self.filename = filename
        HgRepoListModel.__init__(self, repo, '', [], False, parent)

    def _initGraph(self):
        grapher = graph.filelog_grapher(self.repo, self.filename)
        self.graph = graph.Graph(self.repo, grapher)
        QTimer.singleShot(0, self, SIGNAL('filled()'))

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(ALLCOLUMNS)

    def indexLinkedFromRev(self, rev):
        """Index for the last changed revision before the specified revision

        This does not follow renames.
        """
        # as of Mercurial 2.6, workingfilectx.linkrev() does not work, and
        # this model has no virtual working-dir revision.
        if rev is None:
            rev = '.'
        try:
            fctx = self.repo[rev][self.filename]
        except error.LookupError:
            return QModelIndex()
        return self.indexFromRev(fctx.linkrev())

    def fileData(self, index, baseindex=QModelIndex()):
        """Displayable file data at the given index; baseindex specifies the
        revision where status is calculated from"""
        row = index.row()
        if not index.isValid() or row < 0 or row >= len(self.graph):
            return filedata.createNullData(self.repo)
        rev = self.graph[row].rev
        ctx = self.repo.changectx(rev)
        if baseindex.isValid():
            prev = self.graph[baseindex.row()].rev
            pctx = self.repo.changectx(prev)
        else:
            pctx = ctx.p1()
        filename = self.graph.filename(rev)
        if filename in pctx:
            status = 'M'
        else:
            status = 'A'
        return filedata.createFileData(ctx, pctx, filename, status)
