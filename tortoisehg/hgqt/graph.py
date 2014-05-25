# Copyright (c) 2003-2010 LOGILAB S.A. (Paris, FRANCE).
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

"""helper functions and classes to ease hg revision graph building

Based on graphlog's algorithm, with inspiration stolen from TortoiseHg
revision grapher (now stolen back).

The primary interface are the *_grapher functions, which are generators
of Graph instances that describe a revision set graph. These generators
are used by repomodel.py which renders them on a widget.
"""

r"""
How each edge color is determined
=================================

Legends
-------
o, 0, 1, 2, ..., 9
    visible revision
x
    hidden revision
`|a`, `a|` ("a" can be a-z)
    graph edge.
    edges with same alphabet have same color

Rules
-----

A. Edges on the same first-ancestors-line have same color

.. code::

    o
    |a
    o
    |a
    o

B. Edges on branched-merged line have different color from base line

.. code::

    o               o
   a|               |\b
    o               | o
   a|\b            a| |\c
    | o             | | \
    o |b            | |  o
   a| o             o |b |
    |/b            a| | /c
    o               | |/
   a|               | o
    o               o |b
                   a| o
                    |/b
                    o
                   a|
                    o

C. Merged edge has same color as merged-from line

.. code::

   9
   |\    all merged lines(1-3, 4-6, 7-9) and right line(0-1-4-7-9) have
   8 |   same color
   | 7
   6 |
   |\|
   5 |
   | 4
   3 |
   |\|
   2 |
   | 1
   |/
   0

D. Edges on the same first-ancestors-line have same color even if
   separated by revset

.. code::

    4
   a|   Sometimes graph is separated into several parts by revset filter.
    3
    :   All edges on the same first-ancestors-line have same color,
    x   even if they are separated by filter.
    :
    1
   a|
    0

E. Grafted line has different color from source, destination, and
   other grafted lines

.. code::

    5
    |\
   a| \    1-4 and 2-5 are grafted line
    4  \
   a|\c :d
    3 : :
    | : 2
   a| :/b
    | 1
    |/b
    0
"""

import time
import os
import itertools

from mercurial import repoview

from tortoisehg.util import obsoleteutil

LINE_TYPE_PARENT = 0
LINE_TYPE_GRAFT = 1
LINE_TYPE_OBSOLETE = 2

def revision_grapher(repo, opts):
    """incremental revision grapher

    param repo       The repository
    opt   start_rev  Tip-most revision of range to graph
    opt   stop_rev   0-most revision of range to graph
    opt   follow     True means graph only ancestors of start_rev
    opt   revset     set of revisions to graph.
                     If used, then start_rev, stop_rev, and follow is ignored
    opt   branch     Only graph this branch
    opt   allparents If set in addition to branch, then cset outside the
                     branch that are ancestors to some cset inside the branch
                     is also graphed

    This generator function walks through the revision history from
    revision start_rev to revision stop_rev (which must be less than
    or equal to start_rev) and for each revision emits tuples with the
    following elements:

      - current revision
      - column of the current node in the set of ongoing edges
      - color of the node (?)
      - lines: a list of ((col, next_col), edge)
        defining the edges between the current row and the next row
      - parent revisions of current revision
    """

    revset = opts.get('revset', None)
    branch = opts.get('branch', None)
    showhidden = opts.get('showhidden', None)
    showgraftsource = opts.get('showgraftsource', None)
    if showhidden:
        revhidden = []
    else:
        revhidden = repoview.filterrevs(repo, 'visible')
    if revset:
        start_rev = max(revset)
        stop_rev = min(revset)
        follow = False
        hidden = lambda rev: (rev not in revset) or (rev in revhidden)
    else:
        start_rev = opts.get('start_rev', None)
        stop_rev = opts.get('stop_rev', 0)
        follow = opts.get('follow', False)
        hidden = lambda rev: rev in revhidden

    assert start_rev is None or start_rev >= stop_rev

    curr_rev = start_rev
    revs = []
    activeedges = []  # order is not important

    if opts.get('allparents') or not branch:
        def getparents(ctx):
            return [x for x in ctx.parents() if x]
    else:
        def getparents(ctx):
            return [x for x in ctx.parents()
                    if x and x.branch() == branch]

    rev_color = RevColorPalette(getparents)

    while curr_rev is None or curr_rev >= stop_rev:
        if hidden(curr_rev):
            curr_rev -= 1
            continue

        # Compute revs and next_revs.
        ctx = repo[curr_rev]
        if curr_rev not in revs:
            if branch and ctx.branch() != branch:
                if curr_rev is None:
                    curr_rev = len(repo) - 1
                else:
                    curr_rev -= 1
                yield None
                continue

            # New head.
            if start_rev and follow and curr_rev != start_rev:
                curr_rev -= 1
                continue
            revs.append(curr_rev)
        rev_index = revs.index(curr_rev)
        next_revs = revs[:]
        activeedges = [e for e in activeedges if e.endrev < curr_rev]

        # Add parents to next_revs.
        parents = [(p, LINE_TYPE_PARENT, i == 0)
                   for i, p in enumerate(getparents(ctx))
                   if not hidden(p.rev())]
        if showgraftsource:
            src_rev_str = ctx.extra().get('source')
            if src_rev_str is not None and src_rev_str in repo:
                src = repo[src_rev_str]
                src_rev = src.rev()
                if stop_rev <= src_rev < curr_rev and not hidden(src_rev):
                    parents.append((src, LINE_TYPE_GRAFT, False))
            for octx in obsoleteutil.first_known_precursors(ctx):
                src_rev = octx.rev()
                if stop_rev <= src_rev < curr_rev and not hidden(src_rev):
                    parents.append((octx, LINE_TYPE_OBSOLETE, False))
        parents_to_add = []
        for pctx, link_type, is_p1 in parents:
            parent = pctx.rev()
            if parent not in next_revs:
                # Because the parents originate from multiple sources, it is
                # theoretically possible that several point to the same
                # revision.  Only take the first of this (which is graftsource
                # because it is added before).
                if parent in parents_to_add:
                    continue
                parents_to_add.append(parent)
            if is_p1:
                color = rev_color[ctx]
            elif link_type in (LINE_TYPE_GRAFT, LINE_TYPE_OBSOLETE):
                color = rev_color.nextcolor()
            else:
                color = rev_color[pctx]
            activeedges.append(GraphEdge(curr_rev, parent, color, link_type))

        # parents_to_add.sort()
        next_revs[rev_index:rev_index + 1] = parents_to_add

        lines = []
        for e in activeedges:
            if e.startrev == curr_rev:
                r = e.startrev
            else:
                r = e.endrev
            p = (revs.index(r), next_revs.index(e.endrev))
            lines.append((p, e))

        yield GraphNode(curr_rev, rev_index, lines)
        revs = next_revs
        if curr_rev is None:
            curr_rev = len(repo) - 1
        else:
            curr_rev -= 1


def filelog_grapher(repo, path):
    '''
    Graph the ancestry of a single file (log).  Deletions show
    up as breaks in the graph.
    '''
    filerev = len(repo.file(path)) - 1
    fctx = repo.filectx(path, fileid=filerev)
    rev = fctx.rev()

    flog = fctx.filelog()
    heads = [repo.filectx(path, fileid=flog.rev(x)).rev() for x in flog.heads()]
    assert rev in heads
    heads.remove(rev)

    revs = []
    activeedges = []  # order is not important
    rev_color = {}
    nextcolor = 0
    _paths = {}

    while rev >= 0:
        # Compute revs and next_revs
        if rev not in revs:
            revs.append(rev)
            rev_color[rev] = nextcolor ; nextcolor += 1
        curcolor = rev_color[rev]
        index = revs.index(rev)
        next_revs = revs[:]
        activeedges = [e for e in activeedges if e.endrev < rev]

        # Add parents to next_revs
        fctx = repo.filectx(_paths.get(rev, path), changeid=rev)
        for pfctx in fctx.parents():
            _paths[pfctx.rev()] = pfctx.path()
        parents = [pfctx.rev() for pfctx in fctx.parents()]
                   # if f.path() == path]
        parents_to_add = []
        for pno, parent in enumerate(parents):
            if parent not in next_revs:
                parents_to_add.append(parent)
                if pno == 0:
                    rev_color[parent] = curcolor
                else:
                    rev_color[parent] = nextcolor ; nextcolor += 1
            else:
                # at the branch point, we should choose lower color
                # because lower color line is longer than higher one,
                # and probably longer line is major line.
                if pno == 0 and curcolor < rev_color[parent]:
                    rev_color[parent] = curcolor
            if pno == 0:
                color = curcolor
            else:
                color = rev_color[parent]
            activeedges.append(GraphEdge(rev, parent, color))
        parents_to_add.sort()
        next_revs[index:index + 1] = parents_to_add

        lines = []
        for e in activeedges:
            if e.startrev == rev:
                r = e.startrev
            else:
                r = e.endrev
            p = (revs.index(r), next_revs.index(e.endrev))
            lines.append((p, e))

        yield GraphNode(fctx.rev(), index, lines,
                        extra=[_paths.get(fctx.rev(), path)])
        revs = next_revs

        if revs:
            rev = max(revs)
        else:
            rev = -1
        if heads and rev <= heads[-1]:
            rev = heads.pop()

def mq_patch_grapher(repo):
    """Graphs unapplied MQ patches"""
    for patchname in reversed(repo.thgmqunappliedpatches):
        yield GraphNode(patchname, 0, [])

class RevColorPalette(object):
    """Assign node and line colors for each revision"""

    def __init__(self, getparents):
        self._getparents = getparents
        self._pendingheads = []
        self._knowncolors = {}
        self._curcolor = -1

    def _fillpendingheads(self, stoprev):
        if stoprev is None:
            return  # avoid filling everything (int_rev < None is False)

        nextpendingheads = []
        for p_ctxs, color in self._pendingheads:
            pending = self._fillancestors(p_ctxs, color, stoprev)
            if pending:
                nextpendingheads.append((pending, color))
        self._pendingheads = nextpendingheads

    def _fillancestors(self, p_ctxs, curcolor, stoprev):
        while p_ctxs:
            ctx0 = p_ctxs[0]
            rev0 = ctx0.rev()
            if rev0 < stoprev:
                return p_ctxs
            if rev0 in self._knowncolors:
                return
            self._knowncolors[rev0] = curcolor
            p_ctxs = self._getparents(ctx0)

    def nextcolor(self):
        self._curcolor += 1
        return self._curcolor

    def __getitem__(self, ctx):
        rev = ctx.rev()
        if rev not in self._knowncolors:
            self._fillpendingheads(rev)
            if rev not in self._knowncolors:
                color = self.nextcolor()
                self._knowncolors[rev] = color
                p_ctxs = self._getparents(ctx)
                self._pendingheads.append((p_ctxs, color))
        return self._knowncolors[rev]

class GraphEdge(tuple):
    __slots__ = ()
    def __new__(cls, startrev, endrev, color, linktype=LINE_TYPE_PARENT):
        return tuple.__new__(cls, (startrev, endrev, color, linktype))
    @property
    def startrev(self):
        return self[0]  # int or None (for working rev)
    @property
    def endrev(self):
        return self[1]  # int
    @property
    def color(self):
        return self[2]  # int
    @property
    def linktype(self):
        return self[3]  # one of LINE_TYPE
    def __repr__(self):
        xs = (self.__class__.__name__,) + self
        return '%s(%r->%r, color=%r, linktype=%r)' % xs

    @property
    def importance(self):
        """Sort key of overlapped edges; highest one should be drawn last"""
        # prefer parent-child relation and younger (i.e. longer) edge
        return -self[3], -self[2]

class GraphNode(object):
    """
    Simple class to encapsulate a hg node in the revision graph. Does
    nothing but declaring attributes.
    """
    __slots__ = ["rev", "x", "bottomlines", "toplines", "extra"]
    def __init__(self, rev, xposition, lines, extra=None):
        self.rev = rev
        self.x = xposition
        self.bottomlines = lines
        self.toplines = []
        self.extra = extra
    @property
    def cols(self):
        xs = [self.x]
        for p, _e in self.bottomlines:
            xs.extend(p)
        return max(xs) + 1

class Graph(object):
    """
    Graph object to ease hg repo navigation. The Graph object
    instantiate a `revision_grapher` generator, and provide a `fill`
    method to build the graph progressively.
    """

    def __init__(self, repo, grapher, include_mq=False):
        self.repo = repo
        self.maxlog = len(repo)
        if include_mq:
            patch_grapher = mq_patch_grapher(self.repo)
            self.grapher = itertools.chain(patch_grapher, grapher)
        else:
            self.grapher = grapher
        self.nodes = []
        self.nodesdict = {}
        self.max_cols = 0

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            # XXX TODO: ensure nodes are built
            return self.nodes.__getitem__(idx)
        if idx >= len(self.nodes):
            # build as many graph nodes as required to answer the
            # requested idx
            self.build_nodes(idx)
        if idx >= len(self):
            return self.nodes[-1]
        return self.nodes[idx]

    def __len__(self):
        # len(graph) is the number of actually built graph nodes
        return len(self.nodes)

    def build_nodes(self, nnodes=None, rev=None):
        """
        Build up to `nnodes` more nodes in our graph, or build as many
        nodes required to reach `rev`.

        If both rev and nnodes are set, build as many nodes as
        required to reach rev plus nnodes more.
        """
        if self.grapher is None:
            return False

        usetimer = nnodes is None and rev is None
        if usetimer:
            if os.name == "nt":
                timer = time.clock
            else:
                timer = time.time
            startsec = timer()

        stopped = False
        mcol = set([self.max_cols])

        for gnode in self.grapher:
            if gnode is None:
                continue
            if not type(gnode.rev) == str and gnode.rev >= self.maxlog:
                continue
            if self.nodes:
                gnode.toplines = self.nodes[-1].bottomlines
            self.nodes.append(gnode)
            self.nodesdict[gnode.rev] = gnode
            mcol.add(gnode.cols)
            if (rev is not None and isinstance(gnode.rev, int)
                and gnode.rev <= rev):
                rev = None # we reached rev, switching to nnode counter
            if rev is None:
                if nnodes is not None:
                    nnodes -= 1
                    if not nnodes:
                        break
            if usetimer:
                cursec = timer()
                if cursec < startsec or cursec > startsec + 0.1:
                    break
        else:
            self.grapher = None
            stopped = True

        self.max_cols = max(mcol)
        return not stopped

    def isfilled(self):
        return self.grapher is None

    def index(self, rev):
        if len(self) == 0:
            # graph is empty, let's build some nodes.  nodes for unapplied
            # patches are built at once because they don't have comparable
            # revision numbers, which makes build_nodes() go wrong.
            self.build_nodes(10, len(self.repo) - 1)
        if isinstance(rev, int) and len(self) > 0 and rev < self.nodes[-1].rev:
            self.build_nodes(self.nodes[-1].rev - rev)
        if rev in self.nodesdict:
            return self.nodes.index(self.nodesdict[rev])
        return -1

    #
    # File graph method
    #

    def filename(self, rev):
        return self.nodesdict[rev].extra[0]
