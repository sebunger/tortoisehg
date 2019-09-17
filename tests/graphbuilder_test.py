import tempfile
from nose.tools import *

from mercurial.node import nullrev as X
from mercurial import hg

from tortoisehg.util import hglib

import helpers

def setup():
    global _tmpdir
    _tmpdir = helpers.mktmpdir(__name__)


def createrepo(textgraph):
    path = tempfile.mktemp(dir=_tmpdir)
    helpers.buildgraph(path, textgraph)
    return hg.repository(hglib.loadui(), path)

def test_edge_connection_1():
    repo = createrepo(r"""
      o
     /
    o
    """)
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_edge_connection_2():
    repo = createrepo(r"""
    o
     \
      o
    """)
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_edge_connection_3():
    repo = createrepo(r"""
    o
     \
     /
    o
    """)
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_edge_connection_4():
    repo = createrepo(r"""
    o
     \
      |
      o
    """)
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_edge_connection_5():
    repo = createrepo(r"""
    o
     \
      \
       o
    """)
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_edge_connection_6():
    repo = createrepo(r"""
      o
      |
     /
    o
    """)
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_edge_connection_7():
    repo = createrepo(r"""
       o
      /
     /
    o
    """)
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_edge_connection_8():
    repo = createrepo(r"""
      o
     /
    |
    o
    """)
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_edge_connection_9():
    repo = createrepo(r"""
      o
     /
     \
      o
    """)
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_straight():
    repo = createrepo(r"""
    o
    |
    o
    o # lines which have only "|" can be omitted
    o
    """)
    assert_equal((2, X), repo.changelog.parentrevs(3))
    assert_equal((1, X), repo.changelog.parentrevs(2))
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_branched():
    repo = createrepo(r"""
    o
    |  o
    o /
    |/
    o
    """)
    assert_equal((1, X), repo.changelog.parentrevs(3))
    assert_equal((0, X), repo.changelog.parentrevs(2))
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_merged():
    repo = createrepo(r"""
    4
    |\
    | 3
    |/|
    | 2 [branch=foo]
    1 |
    |/
    0
    """)
    assert_equal((1, 3), repo.changelog.parentrevs(4))
    assert_equal((2, 1), repo.changelog.parentrevs(3))
    assert_equal((0, X), repo.changelog.parentrevs(2))
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_merged_2():
    repo = createrepo(r"""
    3
    2\
    | 1
    |/
    0
    """)
    assert_equal((2, 1), repo.changelog.parentrevs(3))

def test_horizontaledge_1():
    repo = createrepo(r"""
    6
    | 5
    +---4
    3 | |
    |\|/
    | 2 [branch=foo]
    1 |
    |/
    0
    """)
    assert_equal((3, X), repo.changelog.parentrevs(6))
    assert_equal((2, X), repo.changelog.parentrevs(5))
    assert_equal((2, 3), repo.changelog.parentrevs(4))
    assert_equal((1, 2), repo.changelog.parentrevs(3))
    assert_equal((0, X), repo.changelog.parentrevs(2))
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_horizontaledge_2():
    repo = createrepo(r"""
    7
    |   6
    | 5---+     # right to left
    | | | |
    | |/  4
    | 3  /
    +---2       # left to right
    |/
    1
    0
    """)
    assert_equal((1, X), repo.changelog.parentrevs(7))
    assert_equal((3, X), repo.changelog.parentrevs(6))
    assert_equal((3, 4), repo.changelog.parentrevs(5))
    assert_equal((2, X), repo.changelog.parentrevs(4))
    assert_equal((1, X), repo.changelog.parentrevs(3))
    assert_equal((1, X), repo.changelog.parentrevs(2))
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_horizontaledge_double():
    repo = createrepo(r"""
    4
    | +-3-+ [branch=foo]
    | |   2 [branch=foo]
    | |  /
    | | /
    |/ /
    1 /
    |/
    0
    """)
    assert_equal((1, X), repo.changelog.parentrevs(4))
    assert_equal((2, 1), repo.changelog.parentrevs(3))
    assert_equal((0, X), repo.changelog.parentrevs(2))
    assert_equal((0, X), repo.changelog.parentrevs(1))

def test_p1_selection_bybranch_1():
    """treat parent which has same branch as p1"""
    repo = createrepo(r"""
    3 [branch=foo]
    |\
    2 |
    | 1 [branch=foo]
    |/
    0
    """)
    assert_equal((1, 2), repo.changelog.parentrevs(3))

def test_p1_selection_bybranch_2():
    """treat parent which has same branch as p1"""
    repo = createrepo(r"""
      3 [branch=default]
     /|
    2 |
    | 1 [branch=foo]
    |/
    0
    """)
    assert_equal((2, 1), repo.changelog.parentrevs(3))

def test_p1_selection_bybranch_3():
    """treat parent which has same branch as p1"""
    repo = createrepo(r"""
    +-3--+ [branch=default]
    |   /
    2  /
    | 1 [branch=foo]
    |/
    0
    """)
    assert_equal((2, 1), repo.changelog.parentrevs(3))

def test_p1_selection_bybranch_4():
    """treat parent which has same branch as p1"""
    repo = createrepo(r"""
    +-3--+ [branch=foo]
    |   /
    2  /
    | 1 [branch=foo]
    |/
    0
    """)
    assert_equal((1, 2), repo.changelog.parentrevs(3))

def test_p1_selection_bygraph_1():
    """treat parent under '|' as p1 when can't determine by branch"""
    repo = createrepo(r"""
    3
    |\
    2 |
    | 1
    |/
    0
    """)
    assert_equal((2, 1), repo.changelog.parentrevs(3))

def test_p1_selection_bygraph_2():
    """treat parent under '|' as p1 when can't determine by branch"""
    repo = createrepo(r"""
      3
     /|
    2 |
    | 1
    |/
    0
    """)
    assert_equal((1, 2), repo.changelog.parentrevs(3))

def test_p1_selection_bygraph_3():
    """treat parent under '|' as p1 when can't determine by branch"""
    repo = createrepo(r"""
    3 [branch=default]
    |\
    2 |
    | 1
    |/
    0
    """)
    assert_equal((2, 1), repo.changelog.parentrevs(3))

def test_p1_selection_bygraph_4():
    """treat parent under '|' as p1 when can't determine by branch"""
    repo = createrepo(r"""
      3 [branch=default]
     /|
    2 |
    | 1
    |/
    0
    """)
    assert_equal((1, 2), repo.changelog.parentrevs(3))

def test_p1_selection_bygraph_5():
    """treat parent under '|' as p1 when can't determine by branch"""
    repo = createrepo(r"""
    3
    |\
    2 |
    | 1 [branch=foo]
    |/
    0
    """)
    assert_equal((2, 1), repo.changelog.parentrevs(3))
    assert_equal('default', repo[3].branch())

def test_p1_selection_bygraph_6():
    """treat parent under '|' as p1 when can't determine by branch"""
    repo = createrepo(r"""
      3
     /|
    2 |
    | 1 [branch=foo]
    |/
    0
    """)
    assert_equal((1, 2), repo.changelog.parentrevs(3))
    assert_equal('foo', repo[3].branch())

def test_cross_edge():
    repo = createrepo(r"""
    9
    |           8
    |     7     |
    |   6 |     |
    | 5 |  \   /
    +-------------4
    |/   \  | |
    +-----3 | |
    +-------2 |
    +---------1
    0
    """)
    assert_equal((1, X), repo.changelog.parentrevs(8))
    assert_equal((2, X), repo.changelog.parentrevs(7))
    assert_equal((3, X), repo.changelog.parentrevs(6))
    assert_equal((0, X), repo.changelog.parentrevs(5))

def test_comment():
    repo = createrepo(r"""
    o
    |#o
    |
    o
    """)
    assert_equal(2, len(repo))

def test_branch():
    repo = createrepo(r"""
      4
     /|
    3 |
    |\|
    | 2 [branch=foo]
    1 |
    |/
    0
    """)
    assert_equal("default", repo[0].branch())
    assert_equal("default", repo[1].branch())
    assert_equal("foo", repo[2].branch())
    assert_equal("default", repo[3].branch())
    assert_equal("foo", repo[4].branch())

def test_user():
    repo = createrepo(r"""
    1 [user=bob]
    |
    0
    """)
    assert_equal("alice", repo[0].user())
    assert_equal("bob", repo[1].user())

def test_files():
    repo = createrepo(r"""
    1 [files="foo,bar/baz"]
    |
    0
    """)

    assert_equal({helpers.GraphBuilder.DUMMYFILE, "foo", "bar/baz"},
                 set(repo[1].files()))

def test_file_move():
    repo = createrepo(r"""
    2 [files="foo=>baz/foo2"]
    1 [files="foo,bar"]
    0
    """)
    assert_equal({helpers.GraphBuilder.DUMMYFILE, "foo", "baz/foo2"},
                 set(repo[2].files()))
    assert_equal(
        {helpers.GraphBuilder.DUMMYFILE, ".hgignore", "bar", "baz/foo2"},
        set(repo[2].manifest()))

def test_file_remove():
    repo = createrepo(r"""
    2 [files="foo=>"]
    1 [files="foo,bar"]
    0
    """)
    assert_equal({helpers.GraphBuilder.DUMMYFILE, "foo"},
                 set(repo[2].files()))
    assert_equal({helpers.GraphBuilder.DUMMYFILE, ".hgignore", "bar"},
                 set(repo[2].manifest()))

def _contentgetter(repo, path):
    return lambda rev: repo[rev].filectx(path).data()

def test_merge():
    repo = createrepo(r"""
    3
    |\
    | 2 [branch=x files=foo]
    1 | [files=foo]
    |/
    0
    """)
    foo = _contentgetter(repo, "foo")
    ok_(foo(1) != foo(2))
    ok_(foo(1) != foo(3))
    ok_(foo(2) != foo(3))
    ok_(foo(3).find("<<<") < 0)

def test_merge_local():
    repo = createrepo(r"""
    3 [merge=local]
    |\
    | 2 [files='foo, bar']
    1 | [files=foo]
    |/
    0
    """)
    foo = _contentgetter(repo, "foo")
    bar = _contentgetter(repo, "bar")
    ok_(foo(1) != foo(2))
    ok_(foo(1) == foo(3))
    ok_(bar(2) == bar(3))

def test_merge_other():
    repo = createrepo(r"""
    3 [merge=other]
    |\
    | 2 [files=foo]
    1 | [files='foo, bar']
    |/
    0
    """)
    foo = _contentgetter(repo, "foo")
    bar = _contentgetter(repo, "bar")
    ok_(foo(1) != foo(2))
    ok_(foo(2) == foo(3))
    ok_(bar(1) == bar(3))


def _sourcerev(repo, rev):
    source = repo[rev].extra()['source']
    return repo[source].rev()

def test_graft():
    repo = createrepo(r"""

    3   [source=2]
    | 2
    1 |
    |/
    0
    """)
    assert_equal((1, X), repo.changelog.parentrevs(3))
    assert_equal((0, X), repo.changelog.parentrevs(2))
    assert_equal((0, X), repo.changelog.parentrevs(1))
    assert_equal(2, _sourcerev(repo, 3))

def test_graft_branch():
    repo = createrepo(r"""
      4 [branch=default]
     /|
    3 | [source=2]
    | 2 [branch=foo]
    1 |
    |/
    0
    """)
    assert_equal((3, 2), repo.changelog.parentrevs(4))
    assert_equal((1, X), repo.changelog.parentrevs(3))
    assert_equal((0, X), repo.changelog.parentrevs(2))
    assert_equal((0, X), repo.changelog.parentrevs(1))
    assert_equal(2, _sourcerev(repo, 3))

def test_graft_local():
    repo = createrepo(r"""
    3   [source=2 merge=local]
    | 2 [files=foo,bar]
    1 | [files=foo]
    |/
    0 [files=foo]
    """)
    foo = _contentgetter(repo, "foo")
    ok_(foo(1) == foo(3))
    ok_(foo(2) != foo(3))

def test_graft_other():
    repo = createrepo(r"""
    3   [source=2 merge=other]
    | 2 [files=foo]
    1 | [files=foo]
    |/
    0 [files=foo]
    """)
    foo = _contentgetter(repo, "foo")
    ok_(foo(1) != foo(3))
    ok_(foo(2) == foo(3))

def test_graft_user():
    repo = createrepo(r"""
    3   [source=2 user=bob]
    | 2
    1 |
    |/
    0
    """)
    assert_equal("bob", repo[3].user())

def shouldraiseerror(graph, expected):
    # we can't use `with assert_raises()` because `with` is not supported
    # by Python 2.4
    try:
        createrepo(graph)
        ok_(False, "InvalidGraph should be raised")
    except helpers.InvalidGraph as ex:
        assert_equal(expected, ex.innermessage)

def test_error_multirev():
    shouldraiseerror(r"""
    o o
    |/
    o
    """, "2 or more rev in same line")

def test_error_isolatededge():
    shouldraiseerror(r"""
    o
    |\
    |
    o
    """, "isolated edge")

def test_error_isolatededge_2():
    shouldraiseerror(r"""
    o
    |
    |/
    o
    """, "isolated edge")

def test_error_toomanyparents():
    shouldraiseerror(r"""
      o
     /|
    o |\
    |/  |
    +---o
    o
    """, "too many parents")

def test_error_toomanyparents_2():
    shouldraiseerror(r"""
      o-+
     /| |
    o | |
    |/  |
    +---o
    o
    """, "too many parents")

def test_error_invalidhorizontaledge():
    shouldraiseerror(r"""
    o
    +-+o+
    |/ /
    | /
    |/
    o
    """, "invalid horizontal edge")

def test_error_invalidhorizontaledge_2():
    shouldraiseerror(r"""
    o
    + o
    |/
    o
    """, "invalid horizontal edge")

def test_error_invalidsource_1():
    shouldraiseerror(r"""
    1 [source=1a]
    |
    0
    """, "`source` must be integer")

def test_error_invalidsource_2():
    shouldraiseerror(r"""
    1 [source=2]
    |
    0
    """, "`source` must point past revision")

def test_error_graftwith2parents():
    shouldraiseerror(r"""
    2 [source=1]
    |\
    | 1
    |/
    0
    """, "grafted revision must have only one parent")
