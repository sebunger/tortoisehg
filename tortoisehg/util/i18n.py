# i18n.py - TortoiseHg internationalization code
#
# Copyright 2009 Steve Borho <steve@borho.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

from __future__ import absolute_import

import gettext
import locale
import os

from mercurial import pycompat

from . import paths

if getattr(pycompat, 'TYPE_CHECKING', False):
    from typing import (
        Dict,
        List,
        Optional,
        Text,
    )

_localeenvs = ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG')
def _defaultlanguage():
    if os.name != 'nt' or any(e in os.environ for e in _localeenvs):
        return  # honor posix-style env var

    # On Windows, UI language can be determined by GetUserDefaultUILanguage(),
    # but gettext doesn't take it into account.
    # Note that locale.getdefaultlocale() uses GetLocaleInfo(), which may be
    # different from UI language.
    #
    # For details, please read "User Interface Language Management":
    # http://msdn.microsoft.com/en-us/library/dd374098(v=VS.85).aspx
    try:
        from ctypes import windll  # pytype: disable=import-error
        langid = windll.kernel32.GetUserDefaultUILanguage()
        return locale.windows_locale[langid]
    except (ImportError, AttributeError, KeyError):
        pass

# to be set later; don't assign these functions directly since they could
# already be imported by name.
_ugettext = None
_ungettext = None

def setlanguage(lang=None):
    # type: (Optional[Text]) -> None
    """Change translation catalog to the specified language"""
    global t, language
    if not lang:
        lang = _defaultlanguage()
    opts = {}
    if lang:
        opts['languages'] = (lang,)
    t = gettext.translation('tortoisehg', paths.get_locale_path(),
                            fallback=True, **opts)
    global _ugettext, _ungettext
    try:
        _ugettext = t.ugettext
        _ungettext = t.ungettext
    except AttributeError:
        _ugettext = t.gettext
        _ungettext = t.ngettext

    language = lang or locale.getdefaultlocale(_localeenvs)[0]  # type: Text
setlanguage()

def availablelanguages():
    # type: () -> List[str]
    """List up language code of which message catalog is available"""
    basedir = paths.get_locale_path()
    def mopath(lang):
        return os.path.join(basedir, lang, 'LC_MESSAGES', 'tortoisehg.mo')
    if os.path.exists(basedir): # locale/ is an install option
        langs = [e for e in os.listdir(basedir) if os.path.exists(mopath(e))]
    else:
        langs = []
    langs.append('en')  # means null translation
    return sorted(langs)

def _(message, context=''):
    # type: (Text, Text) -> pycompat.unicode
    if context:
        sep = '\004'
        tmsg = _ugettext(context + sep + message)
        if sep not in tmsg:
            return tmsg
    return _ugettext(message)

def ngettext(singular, plural, n):
    # type: (Text, Text, int) -> pycompat.unicode
    return _ungettext(singular, plural, n)

def agettext(message, context=''):
    # type: (Text, Text) -> bytes
    """Translate message and convert to local encoding
    such as 'ascii' before being returned.

    Only use this if you need to output translated messages
    to command-line interface (ie: Windows Command Prompt).
    """
    try:
        from tortoisehg.util import hglib
        u = _(message, context)
        return hglib.fromunicode(u)
    except (LookupError, UnicodeEncodeError):
        return pycompat.sysbytes(message)

class keepgettext(object):
    def _(self, message, context=''):
        # type: (Text, Text) -> Dict[Text, Text]
        return {'id': message, 'str': _(message, context)}
