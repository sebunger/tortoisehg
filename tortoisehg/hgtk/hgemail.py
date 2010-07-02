# hgemail.py - TortoiseHg's dialog for sending patches via email
#
# Copyright 2007 TK Soh <teekaysoh@gmail.com>
# Copyright 2007 Steve Borho <steve@borho.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import os
import gtk
import pango
import tempfile

from mercurial import hg, ui, extensions, error

from tortoisehg.util.i18n import _
from tortoisehg.util import hglib, settings

from tortoisehg.hgtk import gtklib, dialog, thgconfig, hgcmd, textview

class EmailDialog(gtk.Window):
    """ Send patches or bundles via email """
    def __init__(self, root='', revargs=[]):
        """ Initialize the Dialog """
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)

        gtklib.set_tortoise_icon(self, 'hg.ico')
        gtklib.set_tortoise_keys(self)
        self.root = root
        self.revargs = revargs

        self.tbar = gtk.Toolbar()
        self.tips = gtklib.Tooltips()

        tbuttons = [
                self._toolbutton(gtk.STOCK_GOTO_LAST, _('Send'),
                                 self._on_send_clicked,
                                 _('Send emails')),
                self._toolbutton(gtk.STOCK_FIND, _('Test'),
                                 self._on_test_clicked,
                                 _('Show emails which would be sent')),
                gtk.SeparatorToolItem(),
                self._toolbutton(gtk.STOCK_PREFERENCES, _('Configure'),
                                 self._on_conf_clicked,
                                 _('Configure email settings'))
            ]
        for btn in tbuttons:
            self.tbar.insert(btn, -1)
        mainvbox = gtk.VBox()
        self.add(mainvbox)
        mainvbox.pack_start(self.tbar, False, False, 2)

        # set dialog title
        if revargs[0] in ('--outgoing', '-o'):
            self.set_title(_('Email outgoing changes'))
        elif revargs[0] in ('--rev', '-r'):
            self.set_title(_('Email revisions ') + ' '.join(revargs[1:]))
        else:
            self.set_title(_('Email Mercurial Patches'))
        self.set_default_size(650, 450)

        hbox = gtk.HBox()
        envframe = gtk.Frame(_('Envelope'))
        flagframe = gtk.Frame(_('Options'))
        hbox.pack_start(envframe, True, True, 4)
        hbox.pack_start(flagframe, False, False, 4)
        mainvbox.pack_start(hbox, False, True, 4)

        # Envelope settings
        table = gtklib.LayoutTable()
        envframe.add(table)

        ## To: combo box
        self._tolist = gtk.ListStore(str)
        self._tobox = gtk.ComboBoxEntry(self._tolist, 0)
        table.add_row(_('To:'), self._tobox, padding=False)

        ## Cc: combo box
        self._cclist = gtk.ListStore(str)
        self._ccbox = gtk.ComboBoxEntry(self._cclist, 0)
        table.add_row(_('Cc:'), self._ccbox, padding=False)

        ## From: combo box
        self._fromlist = gtk.ListStore(str)
        self._frombox = gtk.ComboBoxEntry(self._fromlist, 0)
        table.add_row(_('From:'), self._frombox, padding=False)

        ## In-Reply-To: entry
        self._replyto = gtk.Entry()
        table.add_row(_('In-Reply-To:'), self._replyto, padding=False)
        self.tips.set_tip(self._replyto,
            _('Message identifier to reply to, for threading'))

        # Options
        table = gtklib.LayoutTable()
        flagframe.add(table)

        self._normal = gtk.RadioButton(None, _('Send changesets as Hg patches'))
        table.add_row(self._normal)
        self.tips.set_tip(self._normal,
                _('Hg patches (as generated by export command) are compatible'
                ' with most patch programs.  They include a header which'
                ' contains the most important changeset metadata.'))

        self._git = gtk.RadioButton(self._normal,
                _('Use extended (git) patch format'))
        table.add_row(self._git)
        self.tips.set_tip(self._git,
                _('Git patches can describe binary files, copies, and'
                ' permission changes, but recipients may not be able to'
                ' use them if they are not using git or Mercurial.'))

        self._plain = gtk.RadioButton(self._normal,
                _('Plain, do not prepend Hg header'))
        table.add_row(self._plain)
        self.tips.set_tip(self._plain,
                _('Stripping Mercurial header removes username and parent'
                ' information.  Only useful if recipient is not using'
                ' Mercurial (and does not like to see the headers).'))

        self._bundle = gtk.RadioButton(self._normal,
                _('Send single binary bundle, not patches'))
        table.add_row(self._bundle)
        if revargs[0] in ('--outgoing', '-o'):
            self.tips.set_tip(self._bundle,
                _('Bundles store complete changesets in binary form.'
                ' Upstream users can pull from them. This is the safest'
                ' way to send changes to recipient Mercurial users.'))
        else:
            self._bundle.set_sensitive(False)
            self.tips.set_tip(self._bundle,
                _('This feature is only available when sending outgoing'
                ' changesets. It is not applicable with revision ranges.'))

        self._attach = gtk.CheckButton(_('attach'))
        self.tips.set_tip(self._attach,
                _('send patches as attachments'))
        self._inline = gtk.CheckButton(_('inline'))
        self.tips.set_tip(self._inline,
                _('send patches as inline attachments'))
        self._diffstat = gtk.CheckButton(_('diffstat'))
        self.tips.set_tip(self._diffstat,
                _('add diffstat output to messages'))
        table.add_row(self._attach, self._inline, self._diffstat, padding=False)

        # Subject combo
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        self._subjlist = gtk.ListStore(str)
        self._subjbox = gtk.ComboBoxEntry(self._subjlist, 0)
        hbox.pack_start(gtk.Label(_('Subject:')), False, False, 4)
        hbox.pack_start(self._subjbox, True, True, 4)

        hglib.loadextension(ui.ui(), 'patchbomb')

        # --flags was added after hg 1.3
        hasflags = False
        for arg in extensions.find('patchbomb').emailopts:
            if arg[1] == 'flag':
                hasflags = True
                break
        self._flaglist = gtk.ListStore(str)
        self._flagbox = gtk.ComboBoxEntry(self._flaglist, 0)
        if hasflags:
            hbox.pack_start(gtk.Label(_('Flags:')), False, False, 4)
            hbox.pack_start(self._flagbox, False, False, 4)
        vbox.pack_start(hbox, False, False, 4)

        # Description TextView
        accelgroup = gtk.AccelGroup()
        self.add_accel_group(accelgroup)
        self.descview = textview.UndoableTextView(accelgroup=accelgroup)
        self.descview.set_editable(True)
        fontcomment = hglib.getfontconfig()['fontcomment']
        self.descview.modify_font(pango.FontDescription(fontcomment))
        self.descbuffer = self.descview.get_buffer()
        scrolledwindow = gtk.ScrolledWindow()
        scrolledwindow.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolledwindow.add(self.descview)
        frame = gtk.Frame(_('Patch Series (Bundle) Description'))
        frame.set_border_width(4)
        vbox.pack_start(scrolledwindow, True, True, 4)
        vbox.set_border_width(4)
        eventbox = gtk.EventBox()
        eventbox.add(vbox)
        frame.add(eventbox)
        self._eventbox = eventbox
        mainvbox.pack_start(frame, True, True, 4)
        gtklib.idle_add_single_call(self._refresh, True)

    def _toolbutton(self, stock, label, handler, tip):
        tbutton = gtk.ToolButton(stock)
        tbutton.set_label(label)
        self.tips.set_tip(tbutton, tip)
        tbutton.connect('clicked', handler)
        return tbutton

    def _refresh(self, initial):
        def fill_history(history, vlist, cpath):
            vlist.clear()
            if cpath not in history.get_keys():
                return
            for v in history.get_value(cpath):
                vlist.append([v])

        history = settings.Settings('email')
        try:
            repo = hg.repository(ui.ui(), path=self.root)
            self.repo = repo
        except error.RepoError:
            self.repo = None
            return

        def getfromaddr(ui):
            """Get sender address in the same manner as patchbomb"""
            addr = ui.config('email', 'from') or ui.config('patchbomb', 'from')
            if addr:
                return addr
            try:
                return repo.ui.username()
            except error.Abort:
                return ''

        if initial:
            # Only zap these fields at startup
            self._tobox.child.set_text(hglib.fromutf(repo.ui.config('email', 'to', '')))
            self._ccbox.child.set_text(hglib.fromutf(repo.ui.config('email', 'cc', '')))
            self._frombox.child.set_text(hglib.fromutf(getfromaddr(repo.ui)))
            self._subjbox.child.set_text(hglib.fromutf(repo.ui.config('email', 'subject', '')))
            self.tips.set_tip(self._eventbox,
                    _('Patch series description is sent in initial summary'
                    ' email with [PATCH 0 of N] subject.  It should describe'
                    ' the effects of the entire patch series.  When emailing'
                    ' a bundle, these fields make up the message subject and'
                    ' body. Flags is a comma separated list of tags'
                    ' which are inserted into the message subject prefix.')
                    )
            gtklib.addspellcheck(self.descview, self.repo.ui)
        fill_history(history, self._tolist, 'email.to')
        fill_history(history, self._cclist, 'email.cc')
        fill_history(history, self._fromlist, 'email.from')
        fill_history(history, self._subjlist, 'email.subject')
        fill_history(history, self._flaglist, 'email.flags')
        if len(self._flaglist) == 0:
            self._flaglist.append(['STABLE'])

    def _on_conf_clicked(self, button):
        dlg = thgconfig.ConfigDialog(False, focus='email.from')
        dlg.show_all()
        dlg.run()
        dlg.hide()
        self._refresh(False)

    def _on_send_clicked(self, button):
        self.send()

    def _on_test_clicked(self, button):
        self.send(True)

    def send(self, test = False):
        def record_new_value(cpath, history, newvalue):
            if not newvalue: return
            if cpath not in history.get_keys():
                history.set_value(cpath, [])
            elif newvalue in history.get_value(cpath):
                history.get_value(cpath).remove(newvalue)
            history.get_value(cpath).insert(0, newvalue)

        totext = hglib.fromutf(self._tobox.child.get_text())
        cctext = hglib.fromutf(self._ccbox.child.get_text())
        fromtext = hglib.fromutf(self._frombox.child.get_text())
        subjtext = hglib.fromutf(self._subjbox.child.get_text())
        flagtext = hglib.fromutf(self._flagbox.child.get_text())
        inreplyto = hglib.fromutf(self._replyto.get_text())

        if not totext:
            dialog.info_dialog(self, _('Info required'),
                        _('You must specify a recipient'))
            self._tobox.grab_focus()
            return
        if not fromtext:
            dialog.info_dialog(self, _('Info required'),
                        _('You must specify a sender address'))
            self._frombox.grab_focus()
            return
        if not self.repo:
            return

        if self.repo.ui.config('email', 'method', 'smtp') == 'smtp' and not test:
            if not self.repo.ui.config('smtp', 'host'):
                dialog.info_dialog(self, _('Info required'),
                            _('You must configure SMTP'))
                dlg = thgconfig.ConfigDialog(False, focus='smtp.host')
                dlg.show_all()
                dlg.run()
                dlg.hide()
                self._refresh(False)
                return

        if not test:
            history = settings.Settings('email')
            record_new_value('email.to', history, totext)
            record_new_value('email.cc', history, cctext)
            record_new_value('email.from', history, fromtext)
            record_new_value('email.subject', history, subjtext)
            record_new_value('email.flags', history, flagtext)
            history.write()

        cmdline = ['hg', 'email', '-f', fromtext, '-t', totext, '-c', cctext]
        oldpager = os.environ.get('PAGER')
        if test:
            if oldpager:
                del os.environ['PAGER']
            cmdline.insert(2, '--test')
        if flagtext:
            flags = [f.strip() for f in flagtext.split(',') if f.strip()]
            for f in flags:
                cmdline += ['--flag', f]
        if subjtext:
            cmdline += ['--subject', subjtext]
        if self._bundle.get_active():
            cmdline += ['--bundle']
            if '--outgoing' in self.revargs:
                self.revargs.remove('--outgoing')
        elif self._plain.get_active():  cmdline += ['--plain']
        elif self._git.get_active():    cmdline += ['--git']
        if self._inline.get_active():   cmdline += ['--inline']
        if self._attach.get_active():   cmdline += ['--attach']
        if self._diffstat.get_active(): cmdline += ['--diffstat']
        if inreplyto:
            cmdline += ['--in-reply-to', inreplyto]
        start = self.descbuffer.get_start_iter()
        end = self.descbuffer.get_end_iter()
        desc = self.descbuffer.get_text(start, end)
        if desc:
            cmdline += ['--intro']
        tmpfile = None
        try:
            if desc or not hasattr(extensions.find('patchbomb'), 'introneeded'):
                # --desc is interpreted differently after hg 1.5
                fd, tmpfile = tempfile.mkstemp(prefix="thg_emaildesc_")
                os.write(fd, desc)
                os.close(fd)
                cmdline += ['--desc', tmpfile]
            cmdline.extend(self.revargs)

            dlg = hgcmd.CmdDialog(cmdline)
            dlg.show_all()
            dlg.run()
            dlg.hide()
        finally:
            if oldpager:
                os.environ['PAGER'] = oldpager
            if tmpfile:
                os.unlink(tmpfile)

