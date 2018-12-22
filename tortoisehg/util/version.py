# version.py - TortoiseHg version
#
# Copyright 2009 Steve Borho <steve@borho.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import os
from mercurial import ui, hg, commands, error
from tortoisehg.util.i18n import _ as _gettext

# TODO: use unicode version globally
def _(message, context=''):
    return _gettext(message, context).encode('utf-8')

def liveversion():
    'Attempt to read the version from the live repository'
    utilpath = os.path.dirname(os.path.realpath(__file__))
    thgpath = os.path.dirname(os.path.dirname(utilpath))
    if not os.path.isdir(os.path.join(thgpath, '.hg')):
        raise error.RepoError(_('repository %s not found') % thgpath)

    u = ui.ui()
    # prevent loading additional extensions
    for k, _v in u.configitems('extensions'):
        u.setconfig('extensions', k, '!')
    repo = hg.repository(u, path=thgpath)

    u.pushbuffer()
    commands.identify(u, repo, id=True, tags=True, rev='.')
    l = u.popbuffer().split()
    while len(l) > 1 and l[-1][0].isalpha(): # remove non-numbered tags
        l.pop()
    if len(l) > 1: # tag found
        version = l[-1]
        if l[0].endswith('+'): # propagate the dirty status to the tag
            version += '+'
    elif len(l) == 1: # no tag found
        u.pushbuffer()
        commands.parents(u, repo, template='{latesttag}+{latesttagdistance}-')
        version = u.popbuffer().rpartition(':')[2] + l[0]
    return repo[None].branch(), version

def version():
    try:
        branch, version = liveversion()
        return version
    except:
        pass
    try:
        import __version__
        return __version__.version
    except ImportError:
        return _('unknown')

def package_version():
    try:
        branch, version = liveversion()
        return _build_package_version(branch, version)
    except:
        pass
    try:
        import __version__
        return _build_package_version('stable', __version__.version)
    except ImportError:
        return _('unknown')

def _build_package_version(branch, version):
    """
    >>> _build_package_version('default', '4.8+10')
    '4.8.5010'
    >>> _build_package_version('stable', '4.8.2+5')
    '4.8.21005'
    >>> _build_package_version('stable', '4.8')
    '4.8.0'
    >>> _build_package_version('stable', '4.8.3')
    '4.8.3'
    >>> _build_package_version('stable', '4.8rc1')
    '4.7.91000'
    >>> _build_package_version('stable', '4.8rc1+2')
    '4.7.91002'
    >>> _build_package_version('stable', '1.0rc0')
    '0.9.90000'
    >>> _build_package_version('stable', '0.1rc0')
    '0.0.90000'
    """
    extra = rc = None
    if '+' in version:
        version, extra = version.split('+', 1)
    if 'rc' in version:
        version, rc = version.split('rc', 1)
        if extra is None:
            extra = '0'  # rc should be a development release

    v = [int(x) for x in version.split('.')]
    if rc:
        v = _decrement_version(v)
    while len(v) < 3:
        v.append(0)
    major, minor, periodic = v

    if extra != None:
        tagdistance = int(extra.split('-', 1)[0])
        periodic *= 10000
        if rc:
            periodic += tagdistance + int(rc) * 1000 + 90000
        elif branch == 'default':
            periodic += tagdistance + 5000
        else:
            periodic += tagdistance + 1000

    return '.'.join([str(x) for x in (major, minor, periodic)])

def _decrement_version(v):
    if not v:
        return v
    v = v[:]
    p = len(v) - 1
    v[p] -= 1
    while p > 0 and v[p] < 0:
        v[p] = 9
        v[p - 1] -= 1
        p -= 1
    return v
