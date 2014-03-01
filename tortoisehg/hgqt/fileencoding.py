# fileencoding.py - utility to handle encoding of file contents in Qt
#
# Copyright 2014 Yuya Nishihara <yuya@tcha.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import codecs

from PyQt4.QtGui import QActionGroup

from mercurial import encoding
from tortoisehg.hgqt.i18n import _

# List of encoding names which are likely used, based on the Chromium
# source <chrome/browser/character_encoding.cc> and the Python documentation
# <http://docs.python.org/2.7/library/codecs.html>.
#
# - no UTF-16 or -32, which is binary in Mercurial
# - no ASCII because it can be represented in other encodings
_ENCODINGNAMES = [
    ('utf-8', _('Unicode')),
    ('iso8859-1', _('Western Europe')),
    ('cp1252', _('Western Europe')),
    ('gbk', _('Unified Chinese')),
    ('big5', _('Traditional Chinese')),
    ('big5hkscs', _('Traditional Chinese')),
    ('euc_kr', _('Korean')),
    ('cp932', _('Japanese')),
    ('euc_jp', _('Japanese')),
    ('iso2022_jp', _('Japanese')),
    ('cp874', _('Thai')),
    ('iso8859-15', _('Western Europe')),
    ('mac-roman', _('Western Europe')),
    ('iso8859-2', _('Central and Eastern Europe')),
    ('cp1250', _('Central and Eastern Europe')),
    ('iso8859-5', _('Cyrillic')),
    ('cp1251', _('Cyrillic')),
    ('koi8-r', _('Russian')),
    ('koi8-u', _('Ukrainian')),
    ('iso8859-7', _('Greek')),
    ('cp1253', _('Greek')),
    ('cp1254', _('Turkish')),
    ('cp1256', _('Arabic')),
    ('iso8859-6', _('Arabic')),
    ('cp1255', _('Hebrew')),
    ('iso8859-8', _('Hebrew')),
    ('cp1258', _('Vietnamese')),
    ('iso8859-4', _('Baltic')),
    ('iso8859-13', _('Baltic')),
    ('cp1257', _('Baltic')),
    ('iso8859-3', _('Southern Europe')),
    ('iso8859-10', _('Nordic')),
    ('iso8859-14', _('Celtic')),
    ('iso8859-16', _('South-Eastern Europe')),
    ]

# map to wider encoding included in the table
_SUBSTMAP = {
    'ascii': 'utf-8',
    'shift_jis': 'cp932',
    }

# i18n: comma-separated list of common encoding names in your locale, e.g.
# "utf-8,shift_jis,euc_jp,iso2022_jp" for "ja" locale.
#
# pick from the following encodings:
# utf-8, iso8859-1, cp1252, gbk, big5, big5hkscs, euc_kr, cp932, euc_jp,
# iso2022_jp, cp874, iso8859-15, mac-roman, iso8859-2, cp1250, iso8859-5,
# cp1251, koi8-r, koi8-u, iso8859-7, cp1253, cp1254, cp1256, iso8859-6,
# cp1255, iso8859-8, cp1258, iso8859-4, iso8859-13, cp1257, iso8859-3,
# iso8859-10, iso8859-14, iso8859-16
_LOCALEENCODINGS = _('$FILE_ENCODINGS').replace('$FILE_ENCODINGS', '')


def canonname(name):
    """Resolve aliases and substitutions of the specified encoding

    >>> canonname('Shift_JIS')
    'cp932'
    >>> canonname('foo')
    Traceback (most recent call last):
      ...
    LookupError: unknown encoding: foo

    the listed names should be canonicalized:
    >>> [(enc, canonname(enc)) for enc, _region in _ENCODINGNAMES
    ...  if enc != canonname(enc)]
    []
    """
    name = codecs.lookup(name).name
    return _SUBSTMAP.get(name, name)

def contentencoding(ui):
    """Preferred encoding of file contents in repository"""
    # assumes web.encoding is the content encoding, not the filename one
    enc = ui.config('web', 'encoding')
    if enc:
        try:
            return canonname(enc)
        except LookupError:
            ui.debug('ignoring invalid web.encoding: %s\n' % enc)
    return canonname(encoding.encoding)

def knownencodings():
    """List of encoding names which are likely used"""
    return [enc for enc, _region in _ENCODINGNAMES]


def createActionGroup(parent):
    group = QActionGroup(parent)
    for enc, region in _ENCODINGNAMES:
        a = group.addAction('%s (%s)' % (region, enc))
        a.setCheckable(True)
        a.setData(enc)
    return group

def addCustomAction(group, name):
    cname = canonname(name)  # will raise LookupError for invalid name
    a = group.addAction(name)
    a.setCheckable(True)
    a.setData(cname)
    return a

def addActionsToMenu(menu, group):
    localeencs = set()
    if _LOCALEENCODINGS:
        localeencs.update(canonname(e) for e in _LOCALEENCODINGS.split(','))
    localeencs.add(canonname(encoding.encoding))

    localeacts = []
    otheracts = []
    for a in group.actions():
        enc = str(a.data().toString())
        if enc in localeencs:
            localeacts.append(a)
        else:
            otheracts.append(a)

    if localeacts:
        menu.addActions(localeacts)
        menu.addSeparator()
    menu.addActions(otheracts)

def findActionByName(group, name):
    cname = canonname(name)
    for a in group.actions():
        if str(a.data().toString()) == cname:
            return a
    raise LookupError('no encoding action: %s' % name)

def checkedActionName(group):
    a = group.checkedAction()
    if not a:
        return ''
    return str(a.data().toString())

def checkActionByName(group, name):
    try:
        a = findActionByName(group, name)
    except LookupError:
        a = addCustomAction(group, name)
    a.setChecked(True)
