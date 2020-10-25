# about.py - About dialog for TortoiseHg
#
# Copyright 2007 TK Soh <teekaysoh@gmail.com>
# Copyright 2007 Steve Borho <steve@borho.org>
# Copyright 2010 Yuki KODAMA <endflow.net@gmail.com>
# Copyright 2010 Johan Samyn <johan.samyn@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.
"""
TortoiseHg About dialog - PyQt4 version
"""

from __future__ import absolute_import

import platform
import re
import sys

from .qtcore import (
    PYQT_VERSION_STR,
    QSettings,
    QSize,
    QT_VERSION_STR,
    QTimer,
    QUrl,
    Qt,
    pyqtSlot,
)
from .qtgui import (
    QDialog,
    QDialogButtonBox,
    QFont,
    QLabel,
    QLayout,
    QPixmap,
    QPlainTextEdit,
    QVBoxLayout,
)
from .qtnetwork import (
    QNetworkAccessManager,
    QNetworkRequest,
)

from mercurial import (
    pycompat,
)

from ..util import (
    hglib,
    paths,
    version,
)
from ..util.i18n import _
from . import qtlib

class AboutDialog(QDialog):
    """Dialog for showing info about TortoiseHg"""

    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)

        self.setWindowIcon(qtlib.geticon('thg'))
        self.setWindowTitle(_('About'))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.vbox = QVBoxLayout()
        self.vbox.setSpacing(8)

        self.logo_lbl = QLabel()
        self.logo_lbl.setMinimumSize(QSize(92, 50))
        self.logo_lbl.setScaledContents(False)
        self.logo_lbl.setAlignment(Qt.AlignCenter)
        self.logo_lbl.setPixmap(QPixmap(qtlib.iconpath('thg_logo_92x50.png')))
        self.vbox.addWidget(self.logo_lbl)

        self.name_version_libs_lbl = QLabel()
        self.name_version_libs_lbl.setText(' ')
        self.name_version_libs_lbl.setAlignment(Qt.AlignCenter)
        self.name_version_libs_lbl.setTextInteractionFlags(
                Qt.TextSelectableByMouse)
        self.vbox.addWidget(self.name_version_libs_lbl)
        self.getVersionInfo()

        self.copyright_lbl = QLabel()
        self.copyright_lbl.setAlignment(Qt.AlignCenter)
        self.copyright_lbl.setText('\n'
                + _('Copyright 2008-2020 Steve Borho and others'))
        self.vbox.addWidget(self.copyright_lbl)
        self.courtesy_lbl = QLabel()
        self.courtesy_lbl.setAlignment(Qt.AlignCenter)
        self.courtesy_lbl.setText(
              _('Several icons are courtesy of the TortoiseSVN and Tango projects') + '\n')
        self.vbox.addWidget(self.courtesy_lbl)

        self.download_url_lbl = QLabel()
        self.download_url_lbl.setMouseTracking(True)
        self.download_url_lbl.setAlignment(Qt.AlignCenter)
        self.download_url_lbl.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
        self.download_url_lbl.setOpenExternalLinks(True)
        self.download_url_lbl.setText('<a href=%s>%s</a>' %
                                      ('https://tortoisehg.bitbucket.io',
                                       _('You can visit our site here')))
        self.vbox.addWidget(self.download_url_lbl)

        # Extra space between the URL and hosting credits
        self.vbox.addWidget(QLabel())

        self.hosting_lbl = QLabel()
        self.hosting_lbl.setAlignment(Qt.AlignCenter)
        self.hosting_lbl.setText(
            _('Hosting donated by %s and %s') % (
                '<a href=https://clever-cloud.com>Clever Cloud</a>',
                '<a href=https://octobus.net>Octobus</a>'
            )
        )
        self.hosting_lbl.setMouseTracking(True)
        self.hosting_lbl.setTextInteractionFlags(
            Qt.LinksAccessibleByMouse
        )
        self.hosting_lbl.setOpenExternalLinks(True)
        self.vbox.addWidget(self.hosting_lbl)

        # Let's have some space between the hosting and the buttons.
        self.blancline_lbl = QLabel()
        self.vbox.addWidget(self.blancline_lbl)

        bbox = QDialogButtonBox(self)
        self.license_btn = bbox.addButton(_('&License'),
                                          QDialogButtonBox.ResetRole)
        self.license_btn.setAutoDefault(False)
        self.license_btn.clicked.connect(self.showLicense)
        self.close_btn = bbox.addButton(QDialogButtonBox.Close)
        self.close_btn.setDefault(True)
        self.close_btn.clicked.connect(self.close)
        self.vbox.addWidget(bbox)

        self.setLayout(self.vbox)
        self.layout().setSizeConstraint(QLayout.SetFixedSize)
        self._readsettings()

        # Spawn it later, so that the dialog gets visible quickly.
        QTimer.singleShot(1000, self.getUpdateInfo)
        self._newverreply = None

    def getVersionInfo(self):
        def make_version(tuple):
            vers = ".".join([str(x) for x in tuple])
            return vers
        thgv = (_('version %s') % version.version())
        libv = (_('with Mercurial-%s, Python-%s, PyQt-%s, Qt-%s') %
                (hglib.hgversion, make_version(sys.version_info[0:3]),
              PYQT_VERSION_STR, QT_VERSION_STR))
        par = ('<p style=\" margin-top:0px; margin-bottom:6px;\">'
                '<span style=\"font-size:%spt; font-weight:600;\">'
                '%s</span></p>')
        name = (par % (14, 'TortoiseHg'))
        thgv = (par % (10, thgv))
        nvl = ''.join([name, thgv, libv])
        self.name_version_libs_lbl.setText(nvl)

    @pyqtSlot()
    def getUpdateInfo(self):
        verurl = 'https://www.mercurial-scm.org/release/tortoisehg/latest.dat'
        # If we use QNetworkAcessManager elsewhere, it should be shared
        # through the application.
        self._netmanager = QNetworkAccessManager(self)
        self._newverreply = self._netmanager.get(QNetworkRequest(QUrl(verurl)))
        self._newverreply.finished.connect(self.uFinished)

    @pyqtSlot()
    def uFinished(self):
        newver = (0,0,0)

        try:
            data = self._newverreply.readAll().data()
        finally:
            self._newverreply.close()
            self._newverreply = None

        # Simulate a User-Agent string for platforms with an entry in the file.
        # https://developers.whatismybrowser.com/useragents/explore/operating_system_name
        useragent = "unknown"
        if sys.platform == 'win32':
            from win32process import (  # pytype: disable=import-error
                IsWow64Process as IsX64
            )
            if IsX64():
                useragent = "Windows WOW64"
            else:
                import struct
                width = struct.calcsize("P") * 8
                useragent = width == 64 and 'Windows x64' or 'Windows'
        elif sys.platform == 'darwin':
            # Mac packages will be universal binaries, but try to include the
            # architecture so that older architectures can eventually be
            # dropped from the current installer, and the last of the older
            # architecture offered independently.
            useragent = "Macintosh"
            arch = platform.processor()
            if arch == 'i386':
                useragent += "; Intel"

        candidates = {}

        # Extra check to ensure the regex returned from the server is safe
        # before using it.
        def _check_regex(p):
            # Clear any simple groups.  Example: ``.*Windows.*(WOW|x)64.*``
            p = re.sub(r"\([0-9A-Za-z|]+\)", "", p)

            # Now the regex should be a simple alphanumeric or wildcards
            return re.match("^[A-Za-z0-9.*]+$", p)

        # https://www.mercurial-scm.org/wiki/Packaging#Version_information_protocol
        # priority \t version \t user-agent-regex \t download url \t desc
        for line in pycompat.sysstr(data).splitlines():
            try:
                parts = line.strip().split("\t")
                pattern = parts[2]

                if not _check_regex(pattern):
                    print("Ignoring upgrade pattern %s" % pattern)
                    continue

                if not re.match(pattern, useragent):
                    continue

                prio = int(parts[0].strip())
                candidates[prio] = (parts[1].strip(), parts[3].strip())
            except (IndexError, ValueError):
                pass

        if not candidates:
            return

        prio = [p for p in sorted(candidates.keys())][0]
        newverstr, upgradeurl = candidates[prio]

        try:
            newver = tuple([int(p) for p in newverstr.split('.')])
            thgv = version.package_version()
            curver = tuple([int(p) for p in thgv.split('.')])
        except ValueError:
            curver = (0,0,0)
        if newver > curver:
            url_lbl = _('A new version of TortoiseHg (%s) '
                        'is ready for download!') % newverstr
            urldata = ('<a href=%s>%s</a>' % (upgradeurl, url_lbl))
            self.download_url_lbl.setText(urldata)

    def showLicense(self):
        ld = LicenseDialog(self)
        ld.exec_()

    def closeEvent(self, event):
        if self._newverreply:
            self._newverreply.abort()
        self._writesettings()
        super(AboutDialog, self).closeEvent(event)

    def _readsettings(self):
        s = QSettings()
        self.restoreGeometry(qtlib.readByteArray(s, 'about/geom'))

    def _writesettings(self):
        s = QSettings()
        s.setValue('about/geom', self.saveGeometry())


class LicenseDialog(QDialog):
    """Dialog for showing the TortoiseHg license"""
    def __init__(self, parent=None):
        super(LicenseDialog, self).__init__(parent)

        self.setWindowIcon(qtlib.geticon('thg'))
        self.setWindowTitle(_('License'))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.resize(700, 400)

        self.lic_txt = QPlainTextEdit()
        self.lic_txt.setFont(QFont('Monospace'))
        self.lic_txt.setTextInteractionFlags(
                Qt.TextSelectableByKeyboard|Qt.TextSelectableByMouse)
        try:
            with open(paths.get_license_path(), 'r') as fp:
                lic = fp.read()
            self.lic_txt.setPlainText(lic)
        except IOError:
            pass

        bbox = QDialogButtonBox(self)
        self.close_btn = bbox.addButton(QDialogButtonBox.Close)
        self.close_btn.clicked.connect(self.close)

        self.vbox = QVBoxLayout()
        self.vbox.setSpacing(6)
        self.vbox.addWidget(self.lic_txt)
        self.vbox.addWidget(bbox)

        self.setLayout(self.vbox)
        self._readsettings()

    def closeEvent(self, event):
        self._writesettings()
        super(LicenseDialog, self).closeEvent(event)

    def _readsettings(self):
        s = QSettings()
        self.restoreGeometry(qtlib.readByteArray(s, 'license/geom'))

    def _writesettings(self):
        s = QSettings()
        s.setValue('license/geom', self.saveGeometry())
