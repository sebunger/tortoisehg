"""Helper functions or classes imported from test case"""

from __future__ import absolute_import

import os
import re
import sys
import tempfile
import time
from collections import defaultdict

from mercurial import (
    pycompat,
)

from nose import tools

from tortoisehg.hgqt.qtcore import (
    QTextCodec,
)

from mercurial import (
    dispatch,
    encoding as encodingmod,
    error,
    pycompat,
)

from tortoisehg.util import hglib

def mktmpdir(prefix):
    """Create temporary directory under HGTMP"""
    return tempfile.mkdtemp('', prefix, os.environ['HGTMP'])

def guessmtimedelay(dir):
    """Guess resolution of mtime to return delay necessary to notice change"""
    fd, path = tempfile.mkstemp(prefix='mtime-', dir=dir)
    try:
        lastmtime = os.fstat(fd).st_mtime
        for _i in pycompat.xrange(2):
            time.sleep(0.01)
            os.utime(path, None)
            mtime = os.fstat(fd).st_mtime
            if lastmtime >= mtime:
                if os.name == 'nt':
                    return 2  # assume fat
                else:
                    return 1  # assume ext3
            lastmtime = mtime
        return 0  # ext4, ufs, ntfs, ...
    finally:
        os.close(fd)
        os.unlink(path)

class EncodingPatcher(object):
    """Temporarily change locale encoding"""

    def __init__(self, encoding, fallbackencoding=None):
        self._newencoding = encoding
        self._newfallbackencoding = fallbackencoding or encoding
        self._patched = False

    def patch(self):
        if self._patched:
            raise Exception('encoding already patched')
        self._origenvencoding = os.environ.get('HGENCODING')
        self._origencoding = encodingmod.encoding
        self._origfallbackencoding = encodingmod.fallbackencoding
        self._orighglibencoding = hglib._encoding
        self._orighglibfallbackencoding = hglib._fallbackencoding
        self._origqtextcodec = QTextCodec.codecForLocale()

        os.environ['HGENCODING'] = self._newencoding
        encodingmod.encoding = self._newencoding
        encodingmod.fallbackencoding = self._newfallbackencoding
        hglib._encoding = self._newencoding
        hglib._fallbackencoding = self._newfallbackencoding
        QTextCodec.setCodecForLocale(
            QTextCodec.codecForName(self._newencoding))
        self._patched = True

    def restore(self):
        if not self._patched:
            raise Exception('encoding not patched')
        if self._origenvencoding is not None:
            os.environ['HGENCODING'] = self._origenvencoding
        encodingmod.encoding = self._origencoding
        encodingmod.fallbackencoding = self._origfallbackencoding
        hglib._encoding = self._orighglibencoding
        hglib._fallbackencoding = self._orighglibfallbackencoding
        QTextCodec.setCodecForLocale(self._origqtextcodec)
        self._patched = False

def patchencoding(encoding, fallbackencoding=None):
    """Change locale encoding and return object to restore"""
    patcher = EncodingPatcher(encoding, fallbackencoding)
    patcher.patch()
    return patcher

# TODO: make this usable for unittest.TestCase?
def with_encoding(encoding, fallbackencoding=None):
    """Decorator for test function to change locale encoding temporarily"""
    patcher = EncodingPatcher(encoding, fallbackencoding)
    return tools.with_setup(patcher.patch, patcher.restore)

class HgClient(object):
    """Mercurial client to set up fixture repository

    >>> hg = HgClient('/tmp/foo')
    >>> def dummydispatch(args):
    ...     print(' '.join(['hg'] + list(args)))
    >>> hg._dispatch = dummydispatch
    >>> if os.name == 'nt':
    ...     hg.path = hg.path[2:].replace(os.sep, '/')
    ...     _wjoin = hg.wjoin
    ...     def wjoin(path):
    ...         return _wjoin(path).replace(os.sep, '/')
    ...     hg.wjoin = wjoin

    >>> hg.init()
    hg init /tmp/foo/
    >>> hg.add('bar')
    hg add --cwd /tmp/foo bar
    >>> hg.commit('-m', 'add bar')
    hg commit --cwd /tmp/foo -m add bar

    >>> hg.wjoin(b'bar/baz')
    '/tmp/foo/bar/baz'
    >>> hg.wjoin(b'/absolute/path')
    Traceback (most recent call last):
      ...
    ValueError: not a relative path: /absolute/path
    """

    def __init__(self, path):
        self.path = os.path.abspath(path)

    def init(self, dest=None):
        """Create a new repository"""
        return self._dispatch(('init', self.wjoin(dest or '')))

    def __getattr__(self, name):
        """Return accessor for arbitrary Mercurial command"""
        def cmd(*args):
            return self._dispatch((name, '--cwd', self.path) + args)
        cmd.__name__ = name
        return cmd

    def _dispatch(self, args):
        # TODO: use hglib in order to avoid pollution of global space?
        origwd = os.getcwd()
        ui = hglib.loadui()
        ui.setconfig('ui', 'strict', True)
        ui.fout = pycompat.bytesio()
        ui.ferr = pycompat.bytesio()
        args = list(args)
        req = dispatch.request(args, ui=ui)
        if hasattr(req, 'earlyoptions'):
            try:
                # hg>=4.5: parse early options at once
                options = dispatch._earlyparseopts(ui, args)
            except (AttributeError, TypeError):
                # hg>=4.4.2: early options must be kept in args
                options = {
                    'config': dispatch._earlygetopt(['--config'], args[:]),
                    'debugger': None,
                }
            req.earlyoptions.update(options)
            dispatch._parseconfig(ui, req.earlyoptions['config'])
        else:
            # hg<4.4.2: early options must be stripped
            dispatch._parseconfig(ui, dispatch._earlygetopt(['--config'], args))
        try:
            result = dispatch._dispatch(req) or 0
            return result, ui.fout.getvalue(), ui.ferr.getvalue()
        finally:
            os.chdir(origwd)

    def ftouch(self, *paths):
        """Create empty file inside the repository"""
        for e in paths:
            self.fwrite(e, '')

    def _fwrite(self, path, content, flag):
        fullpath = self.wjoin(path)
        if not os.path.exists(os.path.dirname(fullpath)):
            os.makedirs(os.path.dirname(fullpath))
        f = open(fullpath, flag)
        try:
            f.write(content)
        finally:
            f.close()

    def fwrite(self, path, content):
        """Write the given content to file"""
        self._fwrite(path, content, 'wb')

    def fappend(self, path, content):
        """Append the given content to file"""
        self._fwrite(path, content, 'ab')

    def fread(self, path):
        """Read content of file"""
        f = open(self.wjoin(path), 'rb')
        try:
            return f.read()
        finally:
            f.close()

    def wjoin(self, path):
        if path.startswith('/'):
            raise ValueError('not a relative path: %s' % path)
        return os.path.join(self.path, path)


class InvalidGraph(Exception):
    def __init__(self, lines, lineno, msg):
        graph = []
        for i, line in enumerate(lines):
            if i == lineno:
                graph.append(line + ' << [NG]')
            else:
                graph.append(line)
        graphtext = '\n'.join(reversed(graph))
        Exception.__init__(self, 'Invalid graph:\n' + graphtext + '\n' + msg)
        self.lines = list(reversed(lines))
        self.errorline = len(lines) - 1 - lineno
        self.innermessage = msg


class InvalidGraphLine(Exception):
    pass


class GraphBuilder(object):
    _re_graphline = re.compile(r"""^
                (?P<graph>[ o0-9|/\\+\-]*)       #graph
                (\s*\[(?P<params>[^#]+)\]\s*)?   #params
                (\#(?P<comment>.*))?             #comment
                $""", re.VERBOSE)

    _re_branchparams = re.compile(r"""
                ([0-9a-z_/:\-]+)                    # key
                \s*=\s*                             # =
                (?:"([^"]*)"|'([^']*)'|([^\s='"]*)) # value
                """, re.I | re.VERBOSE)

    DUMMYFILE = '.dummy'

    def __init__(self, path, textgraph):
        textgraph = textgraph.strip('\n')
        self.lines = [l.rstrip() for l in reversed(textgraph.split('\n'))]
        self.hg = HgClient(path)
        self.hg.init()
        self.hg.fappend('.hgignore', 'syntax: glob\n*.orig\n')
        # to use "hg debugobsolete" and suppress "obsolete feature not enabled"
        self.hg.fappend('.hg/hgrc',
                        '[experimental]\nevolution.createmarkers = 1\n')
        self._branchmap = {}

    def build(self):
        revs = defaultdict(list)
        prevline = ''
        tip = -1
        for i, line in enumerate(self.lines):
            try:
                m = self._re_graphline.match(line)
                if not m:
                    raise InvalidGraphLine('parse error')
                line = m.group('graph')
                if not line:
                    continue
                params = m.group('params')
                revs, tip = self._processline(line, params, prevline, revs, tip)
                prevline = line
            except InvalidGraphLine as ex:
                raise InvalidGraph(self.lines, i, str(ex)), \
                        None, sys.exc_info()[2]
            except error.Abort as ex:
                raise InvalidGraph(self.lines, i, "[Abort] %s" % ex), \
                        None, sys.exc_info()[2]

    @classmethod
    def _parseparams(cls, text):
        """
        parse branch parameters.
        return dict which may contain 'branch', 'user', and 'files'

        >>> _parseparams = GraphBuilder._parseparams
        >>> _parseparams('')
        {}
        >>> # branch
        >>> _parseparams('branch=foo')
        {'branch': 'foo'}
        >>> _parseparams('user=alice')
        {'user': 'alice'}
        >>> _parseparams('merge=local')
        {'merge': 'local'}
        >>> _parseparams('source=0')
        {'source': '0'}
        >>> _parseparams('files=foo/bar')
        {'files': ['foo/bar']}
        >>> _parseparams('files="foo,bar, baz"')
        {'files': ['foo', 'bar', 'baz']}
        >>> _parseparams('files="foo=>bar,baz=>"')
        {'files': ['foo=>bar', 'baz=>']}
        >>> ret = _parseparams('user=alice branch=foo files=bar')
        >>> sorted(ret.items())
        [('branch', 'foo'), ('files', ['bar']), ('user', 'alice')]
        """
        ret = {}
        if text:
            for k, v1, v2, v3 in cls._re_branchparams.findall(text):
                v = v1 or v2 or v3
                if k in ('files', 'precs'):
                    ret[k] = re.split(r',\s*', v)
                elif k in ('branch', 'user', 'merge', 'source'):
                    ret[k] = v
                else:
                    raise InvalidGraphLine('undefined param: %s' % k)
        return ret

    def _findhorizontaledgeroot(self, line, edgeend):
        """
        search index of horizontal edge root from revmark
          | +---o   horizontal edge root means '+' of left fig.
          | | |     revmark means 'o' of left fig.
        """
        roots = [i for (i, c) in enumerate(line) if c == '+']
        if len(roots) > 0:
            if len(roots) > 2:
                raise InvalidGraphLine('invalid horizontal edge')

            indices = roots + [edgeend]
            l, r = min(indices), max(indices)
            if any((l < i < r) != (c == '-') for (i, c) in enumerate(line)
                   if i not in indices):
                raise InvalidGraphLine('invalid horizontal edge')

        return roots

    def _processline(self, line, params, prevline, revs, tip):
        """process one line"""
        next_revs = defaultdict(list)
        committed = False

        iscommit = lambda c: c in 'o0123456789'

        visitededges = set()
        for i, c in sorted(enumerate(line), key=lambda x: iscommit(x[1])):
            parents = []
            if c in '|+-' or iscommit(c):
                parents += revs[i]
                visitededges.add(i)
                if 0 < i and i - 1 < len(prevline) and prevline[i - 1] == '/':
                    parents += revs[i - 1]
                    visitededges.add(i - 1)
                if i < len(prevline) - 1 and prevline[i + 1] == '\\':
                    parents += revs[i + 1]
                    visitededges.add(i + 1)

                if iscommit(c):
                    if committed:
                        raise InvalidGraphLine('2 or more rev in same line')
                    for root in self._findhorizontaledgeroot(line, i):
                        parents += next_revs[root]
                        visitededges.add(root)
                    if len(parents) > 2:
                        raise InvalidGraphLine('too many parents')

                    params = GraphBuilder._parseparams(params)
                    precs = params.pop('precs', [])
                    if params.get('source') is not None:
                        tip = self._graft(tip, parents, **params)
                    else:
                        tip = self._commit(tip, parents, **params)
                    parents = [tip]
                    if precs:
                        self._prune(precs, succ=[tip])
                    committed = True

            elif c == '/':
                parents += revs[i - 1]
                visitededges.add(i - 1)
                if i < len(prevline) and prevline[i] == '\\':
                    parents += revs[i]
                    visitededges.add(i)

            elif c == '\\':
                parents += revs[i + 1]
                visitededges.add(i + 1)
                if i < len(prevline) and prevline[i] == '/':
                    parents += revs[i]
                    visitededges.add(i)

            else:
                continue

            if not parents and c != '-' and tip >= 0:
                raise InvalidGraphLine('isolated edge')

            next_revs[i] = parents

        if (set(i for (i, c) in enumerate(prevline) if c in r'|\/')
            - visitededges):
            raise InvalidGraphLine('isolated edge')

        return next_revs, tip


    def _sortparents(self, parents, rev, branch):
        """move same branch parent first if branch specified explicitly"""
        bm = self._branchmap
        if branch:
            bm[rev] = branch
            parents.sort(key=lambda p: bm[p] != branch)
        else:
            if parents:
                bm[rev] = self._branchmap[parents[0]]
            else:
                bm[rev] = 'default'

    def _runcmd(self, cmd, *args):
            ret, fout, ferr = cmd(*args)
            if ret != 0:
                raise InvalidGraphLine(
                        '\n'.join(['failed to %s' % cmd.__name__, fout, ferr]))

    def _resolveall(self, p1, p2):
        unresolved = [x[2:] for x in self.hg.resolve('-l')[1].split('\n')
                      if x.startswith('U ')]
        for path in unresolved:
            self.hg.fwrite(path, '@%d+@%d' % (p1, p2))
        self._runcmd(self.hg.resolve, '-ma')

    def _commit(self, tip, parents, branch=None, user=None, files=None,
                merge=None, source=None):
        assert(source is None)
        if merge:
            if len(parents) < 2:
                raise InvalidGraphLine('`merge` can be specified to'
                                       ' merged or grafted revision')
            if merge not in ('local', 'other'):
                raise InvalidGraphLine(
                        'value of `merge` must be "local" or "other"')
        hg = self.hg

        nextrev = tip + 1
        self._sortparents(parents, nextrev, branch)

        if parents and tip != parents[0]:
            self._runcmd(hg.update, '-Cr', str(parents[0]))
        if branch:
            self._runcmd(hg.branch, branch, '-f')
        if len(parents) > 1:
            tool = 'internal:' + (merge or 'merge')
            ret = hg.merge('-r', str(parents[1]), '-t', tool)[0]
            if ret:
                self._resolveall(*parents)
        else:
            # change DUMMYFILE every commit
            hg.fwrite(self.DUMMYFILE, '@%d' % nextrev)
        if files:
            for path in files:
                if path == self.DUMMYFILE:
                    raise InvalidGraphLine(
                            'file:%s is used internally' % self.DUMMYFILE)
                paths = path.split('=>', 1)
                if len(paths) == 1:
                    hg.fwrite(path, '@%d' % nextrev)
                elif paths[1]:
                    hg.ftouch(paths[1])  # ensure leading directory existence
                    hg.move(paths[0], paths[1], '-f')
                else:
                    hg.remove(paths[0], '-f')

        user = user or 'alice'
        self._runcmd(hg.commit, '-Am', 'commit #%d' % nextrev, '-u', user)
        return nextrev

    def _graft(self, tip, parents, branch=None, user=None, files=None,
               merge=None, source=None):
        assert(source is not None)
        if merge and merge not in ('local', 'other'):
            raise InvalidGraphLine(
                    'value of `merge` must be "local" or "other"')
        try:
            if not (0 <= int(source) <= tip):
                raise InvalidGraphLine('`source` must point past revision')
        except ValueError:
            raise InvalidGraphLine('`source` must be integer')
        if files or branch:
            raise InvalidGraphLine('`files` and `branch` cannot be specified'
                                   ' with `source`')
        if len(parents) != 1:
            raise InvalidGraphLine('grafted revision must have only one parent')

        hg = self.hg

        nextrev = tip + 1
        self._branchmap[nextrev] = self._branchmap[parents[0]]

        if tip != parents[0]:
            self._runcmd(hg.update, '-Cr', str(parents[0]))
        tool = 'internal:' + (merge or 'merge')
        if user:
            uargs = ['-u', user]
        else:
            uargs = []
        try:
            hg.graft('-r', source, '-t', tool, *uargs)
        except error.Abort:
            self._resolveall(parents[0], int(source))
            self._runcmd(hg.graft, '-c', *uargs)

        return nextrev

    def _getnodeids(self, revs):
        out = self.hg.log('--template', '{node}\n',
                          '-r', ' or '.join(str(r) for r in revs))[1]
        return out.splitlines()

    def _prune(self, revs, succ=None):
        if succ:
            succ = self._getnodeids(succ)
        for n in self._getnodeids(revs):
            self._runcmd(self.hg.debugobsolete, n, *succ)

def buildgraph(path, textgraph):
    """create test repostory with dag specified by graphlog like format

    Example:
        buildgraph('./testrepo', r'''
            o   # string after '#' is treated as comment
            |   #
            4   # <- revno can be used instead of 'o' if revno <= 9
            |   #
            o   # <- if 2 parents exist, one under '|' is treated as p1.
            |\  #
            o | # some parameters can be specified by below format
            | o [branch=test user=bob files='foo,bar']
            |/
            o
            ''')

    Revision parameters:
      branch    branch name. if not specified, use branch of p1
      user      author. if not specified, use 'alice'
      files     files to be modified in the revision
      merge     'local' or 'other'. can be specified to merged revision only
      precs     revisions to be superseded by it (needs obsolete._enabled)
    """
    GraphBuilder(path, textgraph).build()
