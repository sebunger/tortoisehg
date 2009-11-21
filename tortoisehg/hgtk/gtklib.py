# gtklib.py - miscellaneous PyGTK classes and functions for TortoiseHg
#
# Copyright 2008 TK Soh <teekaysoh@gmail.com>
# Copyright 2009 Steve Borho <steve@borho.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2, incorporated herein by reference.

import os
import sys
import gtk
import gobject
import pango
import Queue

from tortoisehg.util.i18n import _
from tortoisehg.util import paths, hglib, thread2

from tortoisehg.hgtk import hgtk, gdialog

if gtk.gtk_version < (2, 14, 0):
    # at least on 2.12.12, gtk widgets can be confused by control
    # char markups (like "&#x1;"), so use cgi.escape instead
    from cgi import escape as markup_escape_text
else:
    from gobject import markup_escape_text

if gobject.pygobject_version <= (2,12,1):
    # http://www.mail-archive.com/tortoisehg-develop@lists.sourceforge.net/msg06900.html
    raise Exception('incompatible version of gobject')

def set_tortoise_icon(window, thgicon):
    ico = paths.get_tortoise_icon(thgicon)
    if ico: window.set_icon_from_file(ico)

def get_thg_modifier():
    if sys.platform == 'darwin':
        return '<Mod1>'
    else:
        return '<Control>'

def set_tortoise_keys(window):
    'Set default TortoiseHg keyboard accelerators'
    if sys.platform == 'darwin':
        mask = gtk.accelerator_get_default_mod_mask()
        mask |= gtk.gdk.MOD1_MASK;
        gtk.accelerator_set_default_mod_mask(mask)
    mod = get_thg_modifier()
    accelgroup = gtk.AccelGroup()
    window.add_accel_group(accelgroup)
    key, modifier = gtk.accelerator_parse(mod+'w')
    window.add_accelerator('thg-close', accelgroup, key, modifier,
            gtk.ACCEL_VISIBLE)
    key, modifier = gtk.accelerator_parse(mod+'q')
    window.add_accelerator('thg-exit', accelgroup, key, modifier,
            gtk.ACCEL_VISIBLE)
    key, modifier = gtk.accelerator_parse('F5')
    window.add_accelerator('thg-refresh', accelgroup, key, modifier,
            gtk.ACCEL_VISIBLE)
    key, modifier = gtk.accelerator_parse(mod+'r')
    window.add_accelerator('thg-refresh', accelgroup, key, modifier,
            gtk.ACCEL_VISIBLE)
    key, modifier = gtk.accelerator_parse(mod+'Return')
    window.add_accelerator('thg-accept', accelgroup, key, modifier,
            gtk.ACCEL_VISIBLE)

    # connect ctrl-w and ctrl-q to every window
    window.connect('thg-close', thgclose)
    window.connect('thg-exit', thgexit)

def thgexit(window):
    if thgclose(window):
        gobject.idle_add(hgtk.thgexit, window)

def thgclose(window):
    if hasattr(window, 'should_live'):
        if window.should_live():
            return False
    window.destroy()
    return True

class MessageDialog(gtk.Dialog):
    button_map = {
            gtk.BUTTONS_NONE: None,
            gtk.BUTTONS_OK: (gtk.STOCK_OK, gtk.RESPONSE_OK),
            gtk.BUTTONS_CLOSE : (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE),
            gtk.BUTTONS_CANCEL: (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL),
            gtk.BUTTONS_YES_NO : (gtk.STOCK_YES, gtk.RESPONSE_YES,
                    gtk.STOCK_NO, gtk.RESPONSE_NO),
            gtk.BUTTONS_OK_CANCEL: (gtk.STOCK_OK, gtk.RESPONSE_OK,
                    gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL),
    }
    image_map = {
            gtk.MESSAGE_INFO : gtk.STOCK_DIALOG_INFO,
            gtk.MESSAGE_WARNING : gtk.STOCK_DIALOG_WARNING,
            gtk.MESSAGE_QUESTION : gtk.STOCK_DIALOG_QUESTION,
            gtk.MESSAGE_ERROR : gtk.STOCK_DIALOG_ERROR,
    }

    def __init__(self, parent=None, flags=0, type=gtk.MESSAGE_INFO,
            buttons=gtk.BUTTONS_NONE, message_format=None):
        gtk.Dialog.__init__(self,
                parent=parent,
                flags=flags | gtk.DIALOG_NO_SEPARATOR,
                buttons=MessageDialog.button_map[buttons])
        self.set_resizable(False)

        hbox = gtk.HBox()
        self._image_frame = gtk.Frame()
        self._image_frame.set_shadow_type(gtk.SHADOW_NONE)
        self._image = gtk.Image()
        self._image.set_from_stock(MessageDialog.image_map[type],
                gtk.ICON_SIZE_DIALOG)
        self._image_frame.add(self._image)
        hbox.pack_start(self._image_frame, padding=5)

        lblbox = gtk.VBox(spacing=10)
        self._primary = gtk.Label("")
        self._primary.set_alignment(0.0, 0.5)
        self._primary.set_line_wrap(True)
        lblbox.pack_start(self._primary)

        self._secondary = gtk.Label()
        lblbox.pack_end(self._secondary)
        self._secondary.set_line_wrap(True)
        hbox.pack_start(lblbox, padding=5)

        self.vbox.pack_start(hbox, False, False, 10)
        self.show_all()

    def set_markup(self, s):
        self._primary.set_markup(s)

    def format_secondary_markup(self, message_format):
        self._secondary.set_markup(message_format)

    def format_secondary_text(self, message_format):
        self._secondary.set_text(message_format)

    def set_image(self, image):
        self._image_frame.remove(self._image)
        self._image = image
        self._image_frame.add(self._image)
        self._image.show()

class NativeSaveFileDialogWrapper:
    """Wrap the windows file dialog, or display default gtk dialog if
    that isn't available"""
    def __init__(self, initial = None, title = _('Save File'),
                 filter = ((_('All files'), '*.*'),), filterindex = 1,
                 filename = '', open=False):
        if initial is None:
            initial = os.path.expanduser("~")
        self.initial = initial
        self.filename = filename
        self.title = title
        self.filter = filter
        self.filterindex = filterindex
        self.open = open

    def run(self):
        """run the file dialog, either return a file name, or False if
        the user aborted the dialog"""
        try:
            import win32gui, win32con, pywintypes            
            filepath = self.runWindows()
        except ImportError:
            filepath = self.runCompatible()
        if self.open:
            return filepath
        elif filepath:
            return self.overwriteConfirmation(filepath)
        else:
            return False

    def runWindows(self):

        def rundlg(q):
            import win32gui, win32con, pywintypes
            cwd = os.getcwd()
            fname = None
            try:
                f = ''
                for name, mask in self.filter:
                    f += '\0'.join([name, mask,''])
                opts = dict(InitialDir=self.initial,
                        Flags=win32con.OFN_EXPLORER,
                        File=self.filename,
                        DefExt=None,
                        Title=hglib.fromutf(self.title),
                        Filter= hglib.fromutf(f),
                        CustomFilter=None,
                        FilterIndex=self.filterindex)
                if self.open:
                    fname, _, _ = win32gui.GetOpenFileNameW(**opts)
                else:
                    fname, _, _ = win32gui.GetSaveFileNameW(**opts)
                if fname:
                    fname = os.path.abspath(fname)
            except pywintypes.error:
                pass
            os.chdir(cwd)
            q.put(fname)

        q = Queue.Queue()
        thread = thread2.Thread(target=rundlg, args=(q,))
        thread.start()
        while thread.isAlive():
            # let gtk process events while we wait for rundlg finishing
            gtk.main_iteration(block=True)
        fname = False 
        if q.qsize():
            fname = q.get(0)
        return fname

    def runCompatible(self):
        if self.open:
            action = gtk.FILE_CHOOSER_ACTION_OPEN
            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                       gtk.STOCK_OPEN, gtk.RESPONSE_OK)
        else:
            action = gtk.FILE_CHOOSER_ACTION_SAVE
            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                       gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        dlg = gtk.FileChooserDialog(self.title, None, action, buttons)
        dlg.set_default_response(gtk.RESPONSE_OK)
        dlg.set_current_folder(self.initial)
        if not self.open:
            dlg.set_current_name(self.filename)
        for name, pattern in self.filter:
            fi = gtk.FileFilter()
            fi.set_name(name)
            fi.add_pattern(pattern)
            dlg.add_filter(fi)
        if dlg.run() == gtk.RESPONSE_OK:
            result = dlg.get_filename();
        else:
            result = False
        dlg.destroy()
        return result
    
    def overwriteConfirmation(self, filepath):        
        result = filepath
        if os.path.exists(filepath):
            res = gdialog.Confirm(_('Confirm Overwrite'), [], None,
                _('The file "%s" already exists!\n\n'
                'Do you want to overwrite it?') % filepath).run()
            if res == gtk.RESPONSE_YES:
                os.remove(filepath)
            else:                
                result = False
        return result

class NativeFolderSelectDialog:
    """Wrap the windows folder dialog, or display default gtk dialog if
    that isn't available"""
    def __init__(self, initial = None, title = _('Select Folder')):
        self.initial = initial or os.getcwd()
        self.title = title

    def run(self):
        """run the file dialog, either return a file name, or False if
        the user aborted the dialog"""
        try:
            import win32com, win32gui, pywintypes
            return self.runWindows()
        except ImportError, e:
            return self.runCompatible()

    def runWindows(self):
    
        def rundlg(q):
            from win32com.shell import shell, shellcon
            import win32gui, pywintypes

            def BrowseCallbackProc(hwnd, msg, lp, data):
                if msg == shellcon.BFFM_INITIALIZED:
                    win32gui.SendMessage(
                        hwnd, shellcon.BFFM_SETSELECTION, 1, data)
                elif msg == shellcon.BFFM_SELCHANGED:
                    # Set the status text of the
                    # For this message, 'lp' is the address of the PIDL.
                    pidl = shell.AddressAsPIDL(lp)
                    try:
                        path = shell.SHGetPathFromIDList(pidl)
                        win32gui.SendMessage(
                            hwnd, shellcon.BFFM_SETSTATUSTEXT, 0, path)
                    except shell.error:
                        # No path for this PIDL
                        pass

            fname = None
            try: 
                flags = shellcon.BIF_EDITBOX | 0x40 #shellcon.BIF_NEWDIALOGSTYLE
                pidl, _, _ = shell.SHBrowseForFolder(
                   0,
                   None,
                   hglib.fromutf(self.title),
                   flags,
                   BrowseCallbackProc, # callback function
                   self.initial)       # 'data' param for the callback
                if pidl:
                    fname = hglib.toutf(shell.SHGetPathFromIDList(pidl))
            except (pywintypes.error, pywintypes.com_error):
                pass
            q.put(fname)

        q = Queue.Queue()
        thread = thread2.Thread(target=rundlg, args=(q,))
        thread.start()
        while thread.isAlive():
            # let gtk process events while we wait for rundlg finishing
            gtk.main_iteration(block=True)
        fname = None
        if q.qsize():
            fname = q.get(0)
        return fname

    def runCompatible(self):
        dialog = gtk.FileChooserDialog(title=None,
                action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,
                         gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        dialog.set_default_response(gtk.RESPONSE_OK)
        response = dialog.run()
        fname = dialog.get_filename()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            return fname
        return None

class NativeFileManager:
    """
    Wrapper for opening the specific file manager; Explorer on Windows,
    Nautilus File Manager on Linux.
    """
    def __init__(self, path):
        self.path = path

    def run(self):
        try:
            import pywintypes
            self.runExplorer()
        except ImportError:
            self.runNautilus()

    def runExplorer(self):
        import subprocess
        subprocess.Popen('explorer "%s"' % self.path)

    def runNautilus(self):
        # TODO implement me!
        pass

def markup(text, **kargs):
    """
    A wrapper function for Pango Markup Language.

    All options must be passed as keywork arguments.
    """
    if len(kargs) == 0:
        return markup_escape_text(str(text))
    attr = ''
    for name, value in kargs.items():
        attr += ' %s="%s"' % (name, value)
    text = markup_escape_text(text)
    return '<span%s>%s</span>' % (attr, text)

class LayoutGroup(object):

    def __init__(self, width=0):
        self.width = width
        self.tables = []

    def add(self, *tables, **kargs):
        self.tables.extend(tables)
        if kargs.get('adjust', True):
            self.adjust(**kargs)

    def adjust(self, force=False):
        def realized():
            '''check all tables realized or not'''
            for table in self.tables:
                if tuple(table.allocation) == (-1, -1, 1, 1):
                    return False
            return True
        def trylater():
            '''retry when occurred "size-allocate" signal'''
            adjusted = [False]
            def allocated(table, rect, hid):
                table.disconnect(hid[0])
                if not adjusted[0] and realized():
                    adjusted[0] = True
                    self.adjust()
            for table in self.tables:
                hid = [None]
                hid[0] = table.connect('size-allocate', allocated, hid)
        # check all realized
        if not force and not realized():
            trylater()
            return
        # find out max width
        max = self.width
        for table in self.tables:
            first = table.get_first_header()
            w = first.allocation.width
            max = w > max and w or max
        # apply width
        for table in self.tables:
            first = table.get_first_header()
            first.set_size_request(max, -1)
            first.size_request()

class LayoutTable(gtk.VBox):
    """
    Provide 2 columns layout table.

    This table has 2 columns; first column is used for header, second
    is used for body. In default, the header will be aligned right and
    the body will be aligned left with expanded padding.
    """

    def __init__(self, **kargs):
        gtk.VBox.__init__(self)

        self.table = gtk.Table(1, 2)
        self.pack_start(self.table)
        self.headers = []

        self.set_default_paddings(kargs.get('xpad', -1),
                                  kargs.get('ypad', -1))
        self.set_default_options(kargs.get('headopts', None),
                                 kargs.get('bodyopts', None))

    def set_default_paddings(self, xpad=None, ypad=None):
        """
        Set default paddings between cells.

        LayoutTable has xpad=4, ypad=2 as preset padding values.

        xpad: Number. Pixcel value of padding for x-axis.
              Use -1 to reset padding to preset value.
              Default: None (no change).
        ypad: Number. Pixcel value of padding for y-axis.
              Use -1 to reset padding to preset value.
              Default: None (no change).
        """
        if xpad is not None:
            self.xpad = xpad >= 0 and xpad or 4
        if ypad is not None:
            self.ypad = ypad >= 0 and ypad or 2

    def set_default_options(self, headopts=None, bodyopts=None):
        """
        Set default options for markups of label.

        In default, LayoutTable doesn't use any markups and set the test
        as plane text.  See markup()'s description for more details of
        option parameters.  Note that if called add_row() with just one
        widget, it will be tried to apply 'bodyopts', not 'headopts'.

        headopts: Dictionary. Options used for markups of gtk.Label.
                  This option is only availabled for the label.
                  The text will be escaped automatically.  Default: None.
        bodyopts: [same as 'headopts']
        """
        self.headopts = headopts
        self.bodyopts = bodyopts

    def get_first_header(self):
        """
        Return the cell at top-left corner if exists.
        """
        if len(self.headers) > 0:
            return self.headers[0]
        return None

    def clear_rows(self):
        for child in self.table.get_children():
            self.table.remove(child)

    def add_row(self, *widgets, **kargs):
        """
        Append a new row to the table.

        widgets: mixed list of widget, string, number or None;
                 i.e. ['host:', gtk.Entry(), 20, 'port:', gtk.Entry()]
                 First item will be header, and the rest will be body
                 after packed into a gtk.HBox.

            widget: Standard GTK+ widget.
            string: Label text, will be converted gtk.Label.
            number: Fixed width padding.
            None: Flexible padding.

        kargs: 'padding', 'expand', 'xpad' and 'ypad' are availabled.

            padding: Boolean. If False, the padding won't append the end
                     of body.  Default: True.
            expand: Number. Position of body element to expand.  If you
                    specify this option, 'padding' option will be changed
                    to False automatically.  Default: -1 (last element).
            xpad: Number. Override default 'xpad' value.
            ypad: [same as 'xpad']
            headopts: Dictionary. Override default 'headopts' value.
            bodyopts: [same as 'headopts']
        """
        if len(widgets) == 0:
            return
        t = self.table
        FLAG = gtk.FILL|gtk.EXPAND
        rows = t.get_property('n-rows')
        t.set_property('n-rows', rows + 1)
        xpad = kargs.get('xpad', self.xpad)
        ypad = kargs.get('ypad', self.ypad)
        hopts = kargs.get('headopts', self.headopts)
        bopts = kargs.get('bodyopts', self.bodyopts)
        def getwidget(obj, opts=None):
            '''element converter'''
            if obj == None:
                return gtk.Label('')
            elif isinstance(obj, (int, long)):
                lbl = gtk.Label('')
                lbl.set_size_request(obj, -1)
                lbl.size_request()
                return lbl
            elif isinstance(obj, basestring):
                if opts is None:
                    lbl = gtk.Label(obj)
                else:
                    obj = markup(obj, **opts)
                    lbl = gtk.Label()
                    lbl.set_markup(obj)
                return lbl
            return obj
        def pack(*widgets, **kargs):
            '''pack some of widgets and return HBox'''
            expand = kargs.get('expand', -1)
            if len(widgets) <= expand:
                expand = -1
            padding = kargs.get('padding', expand == -1)
            if padding is True:
                widgets += (None,)
            expmap = [ w is None for w in widgets ]
            expmap[expand] = True
            widgets = [ getwidget(w, bopts) for w in widgets ]
            hbox = gtk.HBox()
            for i, obj in enumerate(widgets):
                widget = getwidget(obj, bopts)
                pad = i != 0 and 2 or 0
                hbox.pack_start(widget, expmap[i], expmap[i], pad)
            return hbox
        if len(widgets) == 1:
            cols = t.get_property('n-columns')
            widget = pack(*widgets, **kargs)
            t.attach(widget, 0, cols, rows, rows + 1, FLAG, 0, xpad, ypad)
        else:
            first = getwidget(widgets[0], hopts)
            if isinstance(first, gtk.Label):
                first.set_alignment(1, 0.5)
            t.attach(first, 0, 1, rows, rows + 1, gtk.FILL, 0, xpad, ypad)
            self.headers.append(first)
            rest = pack(*(widgets[1:]), **kargs)
            t.attach(rest, 1, 2, rows, rows + 1, FLAG, 0, xpad, ypad)

class SlimToolbar(gtk.HBox):
    """
    Slim Toolbar, allows to add the buttons of menu size.
    """

    def __init__(self, tooltips=None):
        gtk.HBox.__init__(self)
        self.tooltips = tooltips

    def append_stock(self, stock_id, tooltip=None, toggle=False):
        icon = gtk.image_new_from_stock(stock_id, gtk.ICON_SIZE_MENU)
        if toggle:
            button = gtk.ToggleButton()
        else:
            button = gtk.Button()
        button.set_image(icon)
        button.set_relief(gtk.RELIEF_NONE)
        button.set_focus_on_click(False)
        if self.tooltips and tooltip:
            self.tooltips.set_tip(button, tooltip)
        self.append_widget(button, padding=0)
        return button

    def append_widget(self, widget, expand=False, padding=2):
        self.pack_start(widget, expand, expand, padding)

    def append_space(self):
        self.append_widget(gtk.Label(), expand=True, padding=0)

class MenuItems(object):
    '''controls creation of menus by ignoring separators at odd places'''

    def __init__(self):
        self.reset()

    def reset(self):
        self.childs = []
        self.sep = None

    def append(self, child):
        '''appends the child menu item, but ignores odd separators'''
        if isinstance(child, gtk.SeparatorMenuItem):
            if len(self.childs) > 0:
                self.sep = child
        else:
            if self.sep:
                self.childs.append(self.sep)
                self.sep = None
            self.childs.append(child)

    def append_sep(self):
        self.append(gtk.SeparatorMenuItem())

    def create_menu(self):
        '''creates the menu by ignoring any extra separator'''
        res = gtk.Menu()
        for c in self.childs:
            res.append(c)
        self.reset()
        return res

def addspellcheck(textview, ui=None):
    lang = None
    if ui:
        lang = ui.config('tortoisehg', 'spellcheck', None)
    try:
        import gtkspell
        gtkspell.Spell(textview, lang)
    except ImportError:
        pass
    except Exception, e:
        print e
    else:
        def selectlang(senderitem):
            from tortoisehg.hgtk import dialog
            spell = gtkspell.get_from_text_view(textview)
            lang = ''
            while True:
                msg = _('Select language for spell checking.\n\n'
                        'Empty is for the default language.\n'
                        'When all text is highlited, the dictionary\n'
                        'is probably not installed.\n\n'
                        'examples: en, en_GB, en_US')
                if lang:
                    msg = _('Lang "%s" can not be set.\n') % lang + msg
                lang = dialog.entry_dialog(None, msg)
                if lang is None: # cancel
                    return
                lang = lang.strip()
                if not lang:
                    lang = None # set default language from $LANG
                try:
                    spell.set_language(lang)
                    return
                except Exception, e:
                    pass
        def langmenu(textview, menu):
            item = gtk.MenuItem(_('Spell Check Language'))
            item.connect('activate', selectlang)
            menuitems = menu.get_children()[:2]
            x = menuitems[0].get_submenu()
            if len(menuitems) >= 2 and menuitems[1].get_child() is None and menuitems[0].get_submenu():
                # the spellcheck language menu seems to be at the top
                menu.insert(item, 1)
            else:
                sep = gtk.SeparatorMenuItem()
                sep.show()
                menu.append(sep)
                menu.append(item)
            item.show()
        textview.connect('populate-popup', langmenu)

def hasspellcheck():
    try:
        import gtkspell
        gtkspell.Spell
        return True
    except ImportError:
        return False

def idle_add_single_call(f, *args):
    '''wrap function f for gobject.idle_add, so that f is guaranteed to be
    called only once, independent of its return value'''

    class single_call(object):
        def __init__(self, f, args):
           self.f = f
           self.args = args
        def __call__(self):
           self.f(*args)  # ignore return value of f
           return False   # return False to signal: don't call me again

    # functions passed to gobject.idle_add must return False, or they
    # will be called repeatedly. The single_call object wraps f and always
    # returns False when called. So the return value of f doesn't matter,
    # it can even return True (which would lead to gobject.idle_add
    # calling the function again, if used without single_call).
    gobject.idle_add(single_call(f, args))