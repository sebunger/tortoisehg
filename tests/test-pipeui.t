  $ cat <<'EOF' >> $HGRCPATH
  > [ui]
  > interactive = True
  > nontty = True
  > [extensions]
  > tortoisehg.util.pipeui =
  > EOF

  $ cat <<'EOF' > testui.py
  > from mercurial import registrar
  > cmdtable = {}
  > command = registrar.command(cmdtable)
  > @command(b'testwrite', norepo=True)
  > def testwrite(ui):
  >     ui.debug('debug\n')
  >     ui.status('status\n')
  >     ui.warn('warn\n')
  > @command(b'testprogress', norepo=True)
  > def testprogress(ui):
  >     with ui.makeprogress('topic', unit='unit', total=1) as progress:
  >         progress.update(0, 'item')
  > @command(b'testprompt', norepo=True)
  > def testprompt(ui):
  >     ui.prompt('prompt:')
  > @command(b'testpromptchoice', norepo=True)
  > def testpromptchoice(ui):
  >     ui.promptchoice('promptchoice$$ &foo $$ &bar')
  > @command(b'testgetpass', norepo=True)
  > def testgetpass(ui):
  >     ui.getpass('getpass: ')
  > EOF
  $ echo 'testui = testui.py' >> $HGRCPATH

  $ hg testwrite --debug
  \x01 ui.debug (esc)
  debug
  \x01 ui.status (esc)
  status
  \x01 ui.warning (esc)
  warn

  $ hg testprogress
  \x01ui.progress (esc)
  topic\x000\x00item\x00unit\x001\x01ui.progress (esc)
  topic\x00\x00\x00\x00 (no-eol) (esc)

  $ echo y | hg testprompt
  \x01 *ui\.prompt (re)
  prompt:\x00y (\x01 *ui\.promptecho|y) (re)
  y (?)

  $ echo b | hg testpromptchoice
  \x01ui\.promptchoice +ui\.prompt (re)
  promptchoice\$\$ \&foo \$\$ \&bar\x00f (\x01 *ui\.promptecho|b) (re)
  b (?)

  $ echo 1234 | hg testgetpass
  \x01ui\.getpass +ui\.prompt (re)
  getpass:  (no-eol)
