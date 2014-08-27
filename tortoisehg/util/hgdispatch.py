# hgdispatch.py - Mercurial command wrapper for TortoiseHg
#
# Copyright 2007, 2009 Steve Borho <steve@borho.org>
# Copyright 2010 Yuki KODAMA <endflow.net@gmail.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version.

import errno, socket, urllib2, urllib

from mercurial import error, extensions, subrepo, util
from mercurial import dispatch as dispatchmod

from tortoisehg.util import hglib, hgversion
from tortoisehg.util.i18n import agettext as _

testedwith = hgversion.testedwith

def dispatch(ui, args):
    req = dispatchmod.request(args, ui)
    # since hg 2.8 (09573ad59f7b), --config is parsed prior to _dispatch()
    hglib.parseconfigopts(req.ui, req.args)
    try:
        return (_dispatch(dispatchmod._dispatch, req) or 0) & 255
    except error.AmbiguousCommand, inst:
        ui.warn(_("hg: command '%s' is ambiguous:\n    %s\n") %
                (inst.args[0], " ".join(inst.args[1])))
    except error.ParseError, inst:
        if len(inst.args) > 1:
            ui.warn(_("hg: parse error at %s: %s\n") %
                    (inst.args[1], inst.args[0]))
        else:
            ui.warn(_("hg: parse error: %s\n") % inst.args[0])
    except error.LockHeld, inst:
        if inst.errno == errno.ETIMEDOUT:
            reason = _('timed out waiting for lock held by %s') % inst.locker
        else:
            reason = _('lock held by %s') % inst.locker
        ui.warn(_("abort: %s: %s\n") % (inst.desc or inst.filename, reason))
    except error.LockUnavailable, inst:
        ui.warn(_("abort: could not lock %s: %s\n") %
                (inst.desc or inst.filename, inst.strerror))
    except error.CommandError, inst:
        if inst.args[0]:
            ui.warn(_("hg %s: %s\n") % (inst.args[0], inst.args[1]))
        else:
            ui.warn(_("hg: %s\n") % inst.args[1])
    except error.OutOfBandError, inst:
        ui.warn(_("abort: remote error:\n"))
        ui.warn(''.join(inst.args))
    except error.RepoError, inst:
        ui.warn(_("abort: %s!\n") % inst)
    except error.ResponseError, inst:
        ui.warn(_("abort: %s") % inst.args[0])
        if not isinstance(inst.args[1], basestring):
            ui.warn(" %r\n" % (inst.args[1],))
        elif not inst.args[1]:
            ui.warn(_(" empty string\n"))
        else:
            ui.warn("\n%r\n" % util.ellipsis(inst.args[1]))
    except error.RevlogError, inst:
        ui.warn(_("abort: %s!\n") % inst)
    except error.UnknownCommand, inst:
        ui.warn(_("hg: unknown command '%s'\n") % inst.args[0])
    except error.InterventionRequired, inst:
        ui.warn("%s\n" % inst)
        return 1
    except socket.error, inst:
        ui.warn(_("abort: %s!\n") % str(inst))
    except IOError, inst:
        if hasattr(inst, "code"):
            ui.warn(_("abort: %s\n") % inst)
        elif hasattr(inst, "reason"):
            try:  # usually it is in the form (errno, strerror)
                reason = inst.reason.args[1]
            except:  # it might be anything, for example a string
                reason = inst.reason
            ui.warn(_("abort: error: %s\n") % reason)
        elif hasattr(inst, "args") and inst.args[0] == errno.EPIPE:
            if ui.debugflag:
                ui.warn(_("broken pipe\n"))
        elif getattr(inst, "strerror", None):
            if getattr(inst, "filename", None):
                ui.warn(_("abort: %s: %s\n") % (inst.strerror, inst.filename))
            else:
                ui.warn(_("abort: %s\n") % inst.strerror)
        else:
            raise
    except OSError, inst:
        if getattr(inst, "filename", None):
            ui.warn(_("abort: %s: %s\n") % (inst.strerror, inst.filename))
        else:
            ui.warn(_("abort: %s\n") % inst.strerror)

    return 255

# exception handling different from _runcatch()
def _dispatch(orig, req):
    ui = req.ui
    try:
        return orig(req)
    except subrepo.SubrepoAbort, e:
        errormsg = str(e)
        label = 'ui.error'
        if e.subrepo:
            label += ' subrepo=%s' % urllib.quote(e.subrepo)
        ui.write_err(_('abort: ') + errormsg + '\n', label=label)
        if e.hint:
            ui.write_err(_('hint: ') + str(e.hint) + '\n', label=label)
    except util.Abort, e:
        ui.write_err(_('abort: ') + str(e) + '\n', label='ui.error')
        if e.hint:
            ui.write_err(_('hint: ') + str(e.hint) + '\n', label='ui.error')
    except error.RepoError, e:
        ui.write_err(str(e) + '\n', label='ui.error')
    except urllib2.HTTPError, e:
        err = _('HTTP Error: %d (%s)') % (e.code, e.msg)
        ui.write_err(err + '\n', label='ui.error')
    except urllib2.URLError, e:
        err = _('URLError: %s') % str(e.reason)
        try:
            import ssl  # Python 2.6 or backport for 2.5
            if isinstance(e.args[0], ssl.SSLError):
                parts = e.args[0].strerror.split(':')
                if len(parts) == 7:
                    file, line, level, _errno, lib, func, reason = parts
                    if func == 'SSL3_GET_SERVER_CERTIFICATE':
                        err = _('SSL: Server certificate verify failed')
                    elif _errno == '00000000':
                        err = _('SSL: unknown error %s:%s') % (file, line)
                    else:
                        err = _('SSL error: %s') % reason
        except ImportError:
            pass
        ui.write_err(err + '\n', label='ui.error')

    return -1

def uisetup(ui):
    # uisetup() is called after the initial dispatch(), so this only makes an
    # effect on command server
    extensions.wrapfunction(dispatchmod, '_dispatch', _dispatch)
