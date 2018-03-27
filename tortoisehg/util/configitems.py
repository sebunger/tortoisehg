# configitems.py - declaration of TortoiseHg configurations
#
# Copyright 2018 Yuya Nishihara <yuya@tcha.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

from __future__ import absolute_import

from mercurial import (
    registrar,
)

from tortoisehg.util import (
    hgversion,
)

configtable = {}
configitem = registrar.configitem(configtable)

testedwith = hgversion.testedwith

configitem('experimental', 'graph-group-branches', default=False)
configitem('experimental', 'graph-group-branches.firstbranch', default='')
configitem('experimental', 'thg.displaynames', default=None)
configitem('reviewboard', 'browser', default=None)
configitem('reviewboard', 'password', default=None)
configitem('reviewboard', 'repoid', default=None)
configitem('reviewboard', 'server', default=None)
configitem('reviewboard', 'user', default=None)
configitem('tortoisehg', 'activatebookmarks', default='prompt')
configitem('tortoisehg', 'authorcolor', default=False)
configitem('tortoisehg', 'autoinc', default='')
configitem('tortoisehg', 'autoresolve', default=True)
configitem('tortoisehg', 'branchcolors', default=None)
configitem('tortoisehg', 'changeset.link', default=None)
configitem('tortoisehg', 'ciexclude', default='')
configitem('tortoisehg', 'cipushafter', default=None)
configitem('tortoisehg', 'closeci', default=False)
configitem('tortoisehg', 'cmdserver.readtimeout', default=30)
configitem('tortoisehg', 'confirmaddfiles', default=True)
configitem('tortoisehg', 'confirmdeletefiles', default=True)
configitem('tortoisehg', 'confirmpush', default=True)
configitem('tortoisehg', 'deadbranch', default='')
configitem('tortoisehg', 'defaultpush', default='all')
configitem('tortoisehg', 'defaultwidget', default=None)
configitem('tortoisehg', 'editor', default=None)
configitem('tortoisehg', 'engmsg', default=False)
configitem('tortoisehg', 'fontcomment', default=configitem.dynamicdefault)
configitem('tortoisehg', 'fontdiff', default=configitem.dynamicdefault)
configitem('tortoisehg', 'fontlog', default=configitem.dynamicdefault)
configitem('tortoisehg', 'fontoutputlog', default=configitem.dynamicdefault)
configitem('tortoisehg', 'forcerepotab', default=False)
configitem('tortoisehg', 'forcevdiffwin', default=False)
configitem('tortoisehg', 'fullauthorname', default=False)
configitem('tortoisehg', 'fullpath', default=False)
configitem('tortoisehg', 'graphlimit', default=500)
configitem('tortoisehg', 'graphopt', default=False)
configitem('tortoisehg', 'guifork', default=None)
configitem('tortoisehg', 'hidetags', default='')
configitem('tortoisehg', 'immediate', default='')
configitem('tortoisehg', 'initialrevision', default='current')
configitem('tortoisehg', 'initskel', default=None)
configitem('tortoisehg', 'issue.bugtraqparameters', default=None)
configitem('tortoisehg', 'issue.bugtraqplugin', default=None)
configitem('tortoisehg', 'issue.bugtraqtrigger', default=None)
configitem('tortoisehg', 'issue.inlinetags', default=False)
configitem('tortoisehg', 'issue.link', default=None)
configitem('tortoisehg', 'issue.linkmandatory', default=False)
configitem('tortoisehg', 'issue.regex', default=None)
configitem('tortoisehg', 'longsummary', default=False)
configitem('tortoisehg', 'maxdiff', default=None)
configitem('tortoisehg', 'monitorrepo', default='localonly')
configitem('tortoisehg', 'opentabsaftercurrent', default=True)
configitem('tortoisehg', 'postpull', default=None)
configitem('tortoisehg', 'promoteditems', default='commit,log')
configitem('tortoisehg', 'readme', default=None)
configitem('tortoisehg', 'recurseinsubrepos', default=None)
configitem('tortoisehg', 'refreshwdstatus', default='auto')
configitem('tortoisehg', 'shell', default=None)
configitem('tortoisehg', 'showfamilyline', default=True)
configitem('tortoisehg', 'summarylen', default=None)
configitem('tortoisehg', 'tabwidth', default=None)
configitem('tortoisehg', 'tasktabs', default='off')
configitem('tortoisehg', 'ui.language', default=None)
configitem('tortoisehg', 'vdiff', default=None)
configitem('tortoisehg', 'workbench.commit.custom-menu', default=list)
configitem('tortoisehg', 'workbench.custom-toolbar', default=list)
configitem('tortoisehg', 'workbench.filelist.custom-menu', default=list)
configitem('tortoisehg', 'workbench.multipleselection.custom-menu',
           default=list)
configitem('tortoisehg', 'workbench.pairselection.custom-menu', default=list)
configitem('tortoisehg', 'workbench.revdetails.custom-menu', default=list)
configitem('tortoisehg', 'workbench.single', default=True)
configitem('tortoisehg', 'workbench.target-combo', default='auto')
configitem('tortoisehg', 'workbench.task-toolbar', default=list)
