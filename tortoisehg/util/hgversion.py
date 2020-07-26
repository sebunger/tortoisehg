# hgversion.py - Version information for Mercurial
#
# Copyright 2009 Steve Borho <steve@borho.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import re

try:
    # post 1.1.2
    from mercurial import util
    hgversion = util.version()
except AttributeError:
    # <= 1.1.2
    from mercurial import version
    hgversion = version.get_version()

testedwith = b'5.3 5.4'

def checkhgversion(v):
    """range check the Mercurial version"""
    reqvers = testedwith.split()
    v = v.split(b'+')[0]
    if not v or v == b'unknown' or len(v) >= 12:
        # can't make any intelligent decisions about unknown or hashes
        return
    vers = re.split(br'\.|-|rc', v)[:2]
    if len(vers) < 2:
        return
    if b'.'.join(vers) in reqvers:
        return
    return (b'This version of TortoiseHg requires Mercurial version %s.n to '
            b'%s.n, but found %s') % (reqvers[0], reqvers[-1], v)
