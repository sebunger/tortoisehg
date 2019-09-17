  $ cat <<EOF >> $HGRCPATH
  > [extensions]
  > tortoisehg.util.partialcommit =
  > EOF
  $ hg init
  $ echo '^patch$' > .hgignore
  $ cat <<EOF > foo
  > b
  > d
  > EOF
  $ hg ci -Am initial
  adding .hgignore
  adding foo

partial commit:

  $ cat <<EOF > foo
  > a
  > b
  > c
  > d
  > EOF
  $ hg diff --git > patch
  $ cat <<EOF > foo
  > a
  > b
  > c
  > d
  > e
  > EOF
  $ touch bar
  $ hg commit -Am 'insert a and c, new file bar' --partials patch
  adding bar

  $ hg diff --git -c .
  diff --git a/bar b/bar
  new file mode 100644
  diff --git a/foo b/foo
  --- a/foo
  +++ b/foo
  @@ -1,2 +1,4 @@
  +a
   b
  +c
   d

  $ hg diff --git
  diff --git a/foo b/foo
  --- a/foo
  +++ b/foo
  @@ -2,3 +2,4 @@
   b
   c
   d
  +e

renamed:

  $ hg mv foo baz
  $ hg diff --git > patch
  $ echo f >> baz
  $ hg commit -Am 'add e, rename file' --partials patch

  $ hg diff --git -c .
  diff --git a/foo b/baz
  rename from foo
  rename to baz
  --- a/foo
  +++ b/baz
  @@ -2,3 +2,4 @@
   b
   c
   d
  +e

  $ hg diff --git
  diff --git a/baz b/baz
  --- a/baz
  +++ b/baz
  @@ -3,3 +3,4 @@
   c
   d
   e
  +f

flags:

#if execbit
  $ chmod +x baz
  $ hg diff --git > patch
  $ chmod -x baz
  $ hg commit -Am 'add f, set exec bit' --partials patch

  $ hg diff --git -c .
  diff --git a/baz b/baz
  old mode 100644
  new mode 100755
  --- a/baz
  +++ b/baz
  @@ -3,3 +3,4 @@
   c
   d
   e
  +f

  $ hg diff --git
  diff --git a/baz b/baz
  old mode 100755
  new mode 100644
#endif

trivial commit:

  $ hg status
  M baz
  $ hg commit -m trivial
  $ hg status
