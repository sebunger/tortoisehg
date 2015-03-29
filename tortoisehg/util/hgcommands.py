# hgcommands.py - miscellaneous Mercurial commands for TortoiseHg
#
# Copyright 2013, 2014 Yuya Nishihara <yuya@tcha.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import os

from mercurial import cmdutil, extensions, util

from tortoisehg.util import hgversion
from tortoisehg.util.i18n import agettext as _

cmdtable = {}
_mqcmdtable = {}
mqcommand = cmdutil.command(_mqcmdtable)
testedwith = hgversion.testedwith

def postinitskel(ui, repo, hooktype, result, pats, **kwargs):
    """create common files in new repository"""
    assert hooktype == 'post-init'
    if result:
        return
    dest = ui.expandpath(pats and pats[0] or '.')
    skel = ui.config('tortoisehg', 'initskel')
    if skel:
        # copy working tree from user-defined path if any
        skel = util.expandpath(skel)
        for name in os.listdir(skel):
            if name == '.hg':
                continue
            util.copyfiles(os.path.join(skel, name),
                           os.path.join(dest, name),
                           hardlink=False)
        return
    # create .hg* files, mainly to workaround Explorer's problem in creating
    # files with a name beginning with a dot
    open(os.path.join(dest, '.hgignore'), 'a').close()

def _applymovemqpatches(q, after, patches):
    fullindexes = dict((q.guard_re.split(rpn, 1)[0], i)
                       for i, rpn in enumerate(q.fullseries))
    fullmap = {}  # patch: line in series file
    for i, n in sorted([(fullindexes[n], n) for n in patches], reverse=True):
        fullmap[n] = q.fullseries.pop(i)
    del fullindexes  # invalid

    if after is None:
        fullat = 0
    else:
        for i, rpn in enumerate(q.fullseries):
            if q.guard_re.split(rpn, 1)[0] == after:
                fullat = i + 1
                break
        else:
            fullat = len(q.fullseries)  # last ditch (should not happen)
    q.fullseries[fullat:fullat] = (fullmap[n] for n in patches)
    q.parseseries()
    q.seriesdirty = True

@mqcommand('qreorder',
    [('', 'after', '', _('move after the specified patch'))],
    _('[--after PATCH] PATCH...'))
def qreorder(ui, repo, *patches, **opts):
    """move patches to the beginning or after the specified patch"""
    after = opts['after'] or None
    q = repo.mq
    if util.any(n not in q.series for n in patches):
        raise util.Abort(_('unknown patch to move specified'))
    if after in patches:
        raise util.Abort(_('invalid patch position specified'))
    if util.any(q.isapplied(n) for n in patches):
        raise util.Abort(_('cannot move applied patches'))

    if after is None:
        at = 0
    else:
        try:
            at = q.series.index(after) + 1
        except ValueError:
            raise util.Abort(_('patch %s not in series') % after)
    if at < q.seriesend(True):
        raise util.Abort(_('cannot move into applied patches'))

    wlock = repo.wlock()
    try:
        _applymovemqpatches(q, after, patches)
        q.savedirty()
    finally:
        wlock.release()

def uisetup(ui):
    try:
        extensions.find('mq')
        cmdtable.update(_mqcmdtable)
    except KeyError:
        pass
