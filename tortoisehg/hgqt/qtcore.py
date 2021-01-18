# qtcore.py - PyQt4/5 compatibility wrapper
#
# Copyright 2015 Yuya Nishihara <yuya@tcha.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

"""Thin compatibility wrapper for QtCore"""

from __future__ import absolute_import

import os
import sys

def _detectapi():
    candidates = ['PyQt5']
    if not getattr(sys, 'frozen', False):
        api = os.environ.get('THG_QT_API')
        if api:
            return api
    for api in candidates:
        try:
            mod = __import__(api)
            mod.__name__  # get around demandimport
            return api
        except ImportError:
            pass
    return candidates[0]

try:
    from ..util.config import qt_api as QT_API  # pytype: disable=import-error
except (AttributeError, ImportError):
    QT_API = _detectapi()

if QT_API == 'PyQt5':
    from PyQt5.QtCore import *
else:
    raise RuntimeError('unsupported Qt API: %s' % QT_API)
