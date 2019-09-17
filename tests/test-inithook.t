  $ cat <<EOF >> $HGRCPATH
  > [extensions]
  > tortoisehg.util.hgcommands =
  > [hooks]
  > post-init.thgskel = python:tortoisehg.util.hgcommands.postinitskel
  > EOF

  $ hg init foo
  $ ls -a foo
  .
  ..
  .hg
  .hgignore

  $ rm foo/.hgignore
  $ hg init foo
  abort: repository foo already exists!
  [255]
  $ ls -a foo
  .
  ..
  .hg

  $ mkdir bar
  $ cd bar
  $ hg init
  $ ls -a
  .
  ..
  .hg
  .hgignore
  $ cd ..

copy working tree from skel (except .hg):

  $ hg init skel
  $ cd skel
  $ mkdir sub
  $ touch .hgignore README sub/file
  $ hg ci -Am skel
  adding .hgignore
  adding README
  adding sub/file
  $ cd ..

  $ hg init --config tortoisehg.initskel="`pwd`/skel" copy
  $ hg stat -R copy
  ? .hgignore
  ? README
  ? sub/file

  $ hg init --config tortoisehg.initskel="`pwd`/invalidskel" copy2
  error: post-init.thgskel hook raised an exception: [Errno *] * (glob)
  (run with --traceback for stack trace)
