# paths.py - TortoiseHg path utilities
#
# Copyright 2009 Steve Borho <steve@borho.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from __future__ import absolute_import, print_function

import os
import shlex
import sys

import mercurial
from mercurial import (
    encoding,
    pycompat,
)

try:
    # TODO: These are generated a str on non Windows platforms, but can be
    #       filesystem encoded on Windows.
    from .config import (
        bin_path,
        icon_path,
        license_path,
        locale_path,
    )
except ImportError:
    icon_path, bin_path, license_path, locale_path = None, None, None, None

_hg_command = None

if pycompat.TYPE_CHECKING:
    from typing import (
        List,
        Optional,
        overload,
    )

    @overload
    def _find_root(p, dn):
        # type: (str, str) -> str
        pass
    @overload
    def _find_root(p, dn):
        # type: (bytes, bytes) -> bytes
        pass


def _find_root(p, dn):
    while not os.path.isdir(os.path.join(p, dn)):
        oldp = p
        p = os.path.dirname(p)
        if p == oldp:
            return None
        if not os.access(p, os.R_OK):
            return None
    return p

def find_root(path=None):
    # type: (Optional[str]) -> str
    return _find_root(path or os.getcwd(), '.hg')

def find_root_bytes(path=None):
    # type: (Optional[bytes]) -> bytes
    return _find_root(path or encoding.getcwd(), b'.hg')

def get_tortoise_icon(icon):
    # type: (str) -> Optional[str]
    "Find a tortoisehg icon"
    icopath = os.path.join(get_icon_path(), icon)
    if os.path.isfile(icopath):
        return icopath
    else:
        print('icon not found', icon)
        return None

def get_icon_path():
    # type: () -> str
    global icon_path
    return icon_path or os.path.join(get_prog_root(), 'icons')

def get_license_path():
    # type: () -> str
    global license_path
    return license_path or os.path.join(get_prog_root(), 'COPYING.txt')

def get_locale_path():
    # type: () -> str
    global locale_path
    return locale_path or os.path.join(get_prog_root(), 'locale')

def _get_hg_path():
    # type: () -> str
    return os.path.abspath(os.path.join(mercurial.__file__, '..', '..'))

def get_hg_command():
    # type: () -> List[str]
    """List of command to execute hg (equivalent to mercurial.util.hgcmd)"""
    global _hg_command
    if _hg_command is None:
        if 'HG' in os.environ:
            try:
                _hg_command = shlex.split(os.environ['HG'],
                                          posix=(os.name != 'nt'))
            except ValueError:
                _hg_command = [os.environ['HG']]
        else:
            _hg_command = _find_hg_command()
    return _hg_command

if os.name == 'nt':
    import win32file

    def find_in_path(pgmname):
        # type: (str) -> Optional[str]
        "return first executable found in search path"
        global bin_path
        ospath = os.environ['PATH'].split(os.pathsep)
        ospath.insert(0, bin_path or get_prog_root())
        pathext = os.environ.get('PATHEXT', '.COM;.EXE;.BAT;.CMD')
        pathext = pathext.lower().split(os.pathsep)
        for path in ospath:
            ppath = os.path.join(path, pgmname)
            for ext in pathext:
                if os.path.exists(ppath + ext):
                    return ppath + ext
        return None

    def _find_hg_command():
        # type: () -> List[str]
        if hasattr(sys, 'frozen'):
            progdir = get_prog_root()
            exe = os.path.join(progdir, 'hg.exe')
            if os.path.exists(exe):
                return [exe]

        # look for in-place build, i.e. "make local"
        exe = os.path.join(_get_hg_path(), 'hg.exe')
        if os.path.exists(exe):
            return [exe]

        exe = find_in_path('hg')
        if not exe:
            return ['hg.exe']
        if exe.endswith('.bat'):
            # assumes Python script exists in the same directory.  .bat file
            # has problems like "Terminate Batch job?" prompt on Ctrl-C.
            if hasattr(sys, 'frozen'):
                python = find_in_path('python') or 'python'
            else:
                python = sys.executable
            return [python, exe[:-4]]
        return [exe]

    def get_prog_root():
        # type: () -> str
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    def get_thg_command():
        # type: () -> List[str]
        if getattr(sys, 'frozen', False):
            return [sys.executable]
        return [sys.executable] + sys.argv[:1]

    def is_unc_path(path):
        # type: (bytes) -> bool
        # splitdrive() on py2 didn't get UNC support until 2.7.8 in 2014, which
        # means it may not be available on CentOS 7, for example.
        if pycompat.ispy3:
            unc, rest = os.path.splitdrive(path)
            return len(unc) > 2
        else:
            unc, rest = os.path.splitunc(path)
            return bool(unc)

    def is_on_fixed_drive(path):
        # type: (bytes) -> bool
        if is_unc_path(path):
            # All UNC paths (\\host\mount) are considered not-fixed
            return False
        drive, remain = os.path.splitdrive(path)
        if drive:
            drive = pycompat.fsdecode(drive)
            return win32file.GetDriveType(drive) == win32file.DRIVE_FIXED
        else:
            return False

else: # Not Windows

    def find_in_path(pgmname):
        # type: (str) -> Optional[str]
        """ return first executable found in search path """
        global bin_path
        ospath = os.environ['PATH'].split(os.pathsep)
        ospath.insert(0, bin_path or get_prog_root())
        for path in ospath:
            ppath = os.path.join(path, pgmname)
            if os.access(ppath, os.X_OK):
                return ppath
        return None

    def _find_hg_command():
        # type: () -> List[str]
        # look for in-place build, i.e. "make local"
        exe = os.path.join(_get_hg_path(), 'hg')
        if os.path.exists(exe):
            return [exe]

        exe = find_in_path('hg')
        if not exe:
            return ['hg']
        return [exe]

    def get_prog_root():
        # type: () -> str
        path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return path

    def get_thg_command():
        # type: () -> List[str]
        return sys.argv[:1]

    def is_unc_path(path):
        # type: (bytes) -> bool
        return False

    def is_on_fixed_drive(path):
        # type: (bytes) -> bool
        return True

