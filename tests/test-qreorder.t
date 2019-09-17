  $ cat <<EOF >> $HGRCPATH
  > [extensions]
  > mq =
  > tortoisehg.util.hgcommands =
  > EOF

  $ hg init unapplied
  $ cd unapplied
  $ hg qinit -c
  $ hg qnew foo
  $ hg qnew bar
  $ hg qnew baz
  $ hg qnew qux
  $ hg qnew quux
  $ hg qpop -a
  popping quux
  popping qux
  popping baz
  popping bar
  popping foo
  patch queue now empty
  $ hg qguard bar +guard

series file may contain comment or empty line

  $ mv .hg/patches/series .hg/patches/series.orig
  $ echo '# comment' > .hg/patches/series
  $ cat .hg/patches/series.orig >> .hg/patches/series

  $ hg commit --mq -m patches
  $ cd ..


move first:

  $ hg qclone -q unapplied movefirst
  $ cd movefirst
  $ hg qreorder baz
  $ hg qseries
  baz
  foo
  bar
  qux
  quux
  $ cat .hg/patches/series
  baz
  # comment
  foo
  bar #+guard
  qux
  quux
  $ cd ..

move last:

  $ hg qclone -q unapplied movelast
  $ cd movelast
  $ hg qreorder --after quux baz
  $ hg qseries
  foo
  bar
  qux
  quux
  baz
  $ cat .hg/patches/series
  # comment
  foo
  bar #+guard
  qux
  quux
  baz
  $ cd ..

move intersect:

  $ hg qclone -q unapplied moveintersect
  $ cd moveintersect
  $ hg qreorder --after baz bar quux
  $ hg qseries
  foo
  baz
  bar
  quux
  qux
  $ cat .hg/patches/series
  # comment
  foo
  baz
  bar #+guard
  quux
  qux
  $ cd ..


move after applied:

  $ hg qclone -q unapplied moveafterapplied
  $ cd moveafterapplied
  $ hg qpush baz
  applying foo
  patch foo is empty
  skipping bar - guarded by '+guard'
  applying baz
  patch baz is empty
  now at: baz
  $ hg qreorder --after baz quux
  $ hg qseries
  foo
  bar
  baz
  quux
  qux
  $ cd ..

move guarded:

  $ hg qclone -q unapplied moveguarded
  $ cd moveguarded
  $ hg qpush baz
  applying foo
  patch foo is empty
  skipping bar - guarded by '+guard'
  applying baz
  patch baz is empty
  now at: baz
  $ hg qreorder --after baz bar
  $ hg qseries
  foo
  baz
  bar
  qux
  quux
  $ cd ..

move before applied:

  $ hg qclone -q unapplied movebeforeapplied
  $ cd movebeforeapplied
  $ hg qpush baz
  applying foo
  patch foo is empty
  skipping bar - guarded by '+guard'
  applying baz
  patch baz is empty
  now at: baz
  $ hg qreorder --after bar quux
  abort: cannot move into applied patches
  [255]
  $ cd ..

move applied:

  $ hg qclone -q unapplied moveapplied
  $ cd moveapplied
  $ hg qpush baz
  applying foo
  patch foo is empty
  skipping bar - guarded by '+guard'
  applying baz
  patch baz is empty
  now at: baz
  $ hg qreorder --after baz foo
  abort: cannot move applied patches
  [255]
  $ cd ..


unknown patch:

  $ cd unapplied
  $ hg qreorder --after baz unknown
  abort: unknown patch to move specified
  [255]
  $ cd ..

unknown insert pos:

  $ cd unapplied
  $ hg qreorder --after unknown foo
  abort: patch unknown not in series
  [255]
  $ cd ..

self insert pos:

  $ cd unapplied
  $ hg qreorder --after foo foo
  abort: invalid patch position specified
  [255]
  $ cd ..


save:

  $ hg qclone -q unapplied save
  $ cd save
  $ hg qreorder --after baz bar quux
  $ cat .hg/patches/series
  # comment
  foo
  baz
  bar #+guard
  quux
  qux
  $ cd ..
