"""Unit tests of hgqt widgets"""

from __future__ import absolute_import

from nose.plugins.skip import SkipTest

from tortoisehg.hgqt.qtgui import (
    QApplication,
)

def setup():
    if not isinstance(QApplication.instance(), QApplication):
        raise SkipTest
