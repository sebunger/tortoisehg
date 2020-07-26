"""Nose plugin to set up test environment"""

from __future__ import absolute_import

import os
import shutil
import sys
import tempfile

from nose import plugins

# don't import mercurial or tortoisehg before setting up test environment

class HgEnvPlugin(plugins.Plugin):
    """Set up temporary environment"""
    enabled = True
    name = 'hgenv'

    def options(self, parser, env):
        parser.add_option('--keep-tmpdir', action='store_true', default=False,
                          help='Keep temporary directory after running tests')
        parser.add_option('--tmpdir',
                          help=('Put temporary files in the given directory '
                                '(implies --keep-tmpdir)'))

    def configure(self, options, conf):
        self.keep_tmpdir = options.keep_tmpdir or bool(options.tmpdir)
        self.tmpdir = options.tmpdir

    def begin(self):
        if 'mercurial' in sys.modules:
            raise Exception('loaded mercurial module before setting up '
                            'test environment')
        self._setupsyspath()
        self._setuptmpdir()
        self._setupconfigdir()
        self._setuphgrc()
        self._setupmiscenv()
        self._setupqapp()

    def _setupsyspath(self):
        hgpath = os.environ.get('HGPATH')
        if hgpath:
            hgpath = os.path.abspath(hgpath)
            sys.path.insert(1, hgpath)
            os.environ['HGPATH'] = hgpath

        thgpath = os.environ.get('THGPATH')
        if not thgpath:
            thgpath = os.path.join(os.path.dirname(__file__), '..')
        thgpath = os.path.abspath(thgpath)
        sys.path.insert(1, thgpath)
        os.environ['THGPATH'] = thgpath

        # setup PYTHONPATH so that hg process can look up thg modules
        pypath = thgpath
        if 'PYTHONPATH' in os.environ:
            pypath += os.pathsep + os.environ['PYTHONPATH']
        os.environ['PYTHONPATH'] = pypath

    def _setuptmpdir(self):
        if self.tmpdir:
            if os.path.exists(self.tmpdir):
                raise Exception('temp dir %r already exists' % self.tmpdir)
            os.makedirs(self.tmpdir)
        else:
            self.tmpdir = tempfile.mkdtemp('', 'thgtests.')
        os.environ['HGTMP'] = self.tmpdir

    def _setupconfigdir(self):
        self.configdir = os.path.join(self.tmpdir, '.config')
        os.mkdir(self.configdir)
        # these environment variables seem not to affect the running process
        os.environ['APPDATA'] = self.configdir
        os.environ['XDG_CONFIG_HOME'] = self.configdir

    def _setuphgrc(self):
        """Create a fresh hgrc for repeatable result"""
        os.environ['HGRCPATH'] = hgrcpath = os.path.join(self.tmpdir, '.hgrc')
        f = open(hgrcpath, 'w')
        try:
            f.write('[defaults]\n')
            f.write('backout = -d "0 0"\n')
            f.write('commit = -d "0 0"\n')
            f.write('tag = -d "0 0"\n')
            # TODO: run mq-dependent tests in separate process?
            f.write('[extensions]\n')
            f.write('mq=\n')
            f.write('delaylock = %s\n'
                    % os.path.join(os.path.dirname(__file__), 'delaylock.py'))
            # register config defaults
            f.write('tortoisehg.util.configitems=\n')
        finally:
            f.close()

    def _setupmiscenv(self):
        """Reset some common environment variables for repeatable result"""
        os.environ['LANG'] = os.environ['LC_ALL'] = os.environ['LANGUAGE'] = 'C'
        os.environ['TZ'] = 'GMT'
        os.environ['HOME'] = self.tmpdir
        os.environ['EMAIL'] = 'Foo Bar <foo.bar@example.com>'
        os.environ['http_proxy'] = ''
        os.environ['HGUSER'] = 'test'
        os.environ['HGENCODING'] = 'ascii'
        os.environ['HGENCODINGMODE'] = 'strict'
        # suppress "Session management error" on X11
        os.environ['SESSION_MANAGER'] = ''

    def _setupqapp(self):
        from tortoisehg.hgqt.qtcore import QCoreApplication, QSettings
        from tortoisehg.hgqt.qtgui import QApplication

        # Make sure to hold single QApplication instance on memory. Multiple
        # instances will lead crash.
        guienabled = (os.name == 'nt' or sys.platform == 'darwin'
                      or bool(os.environ.get('DISPLAY')))
        appcls = [QCoreApplication, QApplication][guienabled]
        self._qapp = appcls([])

        # settings will be saved at $HGTMP/.config/TortoiseHg/TortoiseHgQt.ini
        self._qapp.setApplicationName('TortoiseHgQt')
        self._qapp.setOrganizationName('TortoiseHg')
        QSettings.setDefaultFormat(QSettings.IniFormat)
        QSettings.setPath(QSettings.IniFormat, QSettings.UserScope,
                          self.configdir)

    def finalize(self, result):
        del self._qapp

        if not self.keep_tmpdir:
            shutil.rmtree(self.tmpdir)