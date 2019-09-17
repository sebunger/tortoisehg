import os
from nose.tools import *

from mercurial import (
    pycompat,
)

from tortoisehg.hgqt import graph, thgrepo
from tortoisehg.util import hglib

import helpers

def setup():
    global _tmpdir
    _tmpdir = helpers.mktmpdir(__name__)

    setup_namedbranch()
    setup_20nodes()
    setup_20patches()
    setup_nestedbranch()
    setup_straightenedbyrevset()
    setup_bulkgraft()
    setup_commonedge()
    setup_manyheads()
    setup_obsolete()
    setup_familyline()
    setup_movedfile()

def openrepo(name):
    return thgrepo.repository(hglib.loadui(), os.path.join(_tmpdir, name))

def buildrepo(name, graphtext):
    path = os.path.join(_tmpdir, name)
    helpers.buildgraph(path, graphtext)

def buildlinetable(grapher, predicate):
    table = {}  # rev: [predicate(edge), ...
    for node in grapher:
        if not node:
            continue
        # draw overlapped lines in the same way as HgRepoListModel
        lt = dict((p, predicate(p, e)) for p, e
                  in sorted(node.bottomlines, key=lambda pe: pe[1].importance))
        # and sort them in (start, end) order
        lines = [l for p, l in sorted(lt.items(), key=lambda pl: pl[0])]
        table[node.rev] = lines
    return table

def buildlinecolortable(grapher):
    return buildlinetable(grapher, lambda p, e: e.color)

def buildlinecolumntable(grapher):
    linktypetags = {
        graph.LINE_TYPE_PARENT: '',
        graph.LINE_TYPE_FAMILY: 'F',
        graph.LINE_TYPE_GRAFT: 'G',
        graph.LINE_TYPE_OBSOLETE: 'O',
    }
    def predicate(p, e):
        return '%d-%d%s' % (p[0], p[1], linktypetags[e.linktype])
    return buildlinetable(grapher, predicate)

def setup_namedbranch():
    buildrepo('named-branch', r"""
        8
        |\  7 [files=data]
        | 6 | [merge=local]
        |/| |
        | 5 | [files=data]
        | 4 | [files=data]
        | | 3 [files=data]
        2 |/ [branch=bar files=data]
        | 1 [files=data]
        |/
        0 [files=data]
    """)

def test_linecolor_unfiltered():
    repo = openrepo('named-branch')
    grapher = graph.revision_grapher(repo, {})
    c0, c1, c2 = 0, 1, 2
    actualtable = buildlinecolortable(grapher)
    expectedtable = {
                              # wt
        None: [c0],           # |
                              # 8
        8: [c0, c1],          # |\
                              # | | 7
        7: [c0, c1, c2],      # | | |
                              # | 6 |
        6: [c0, c0, c1, c2],  # |/| |
                              # | 5 |
        5: [c0, c1, c2],      # | | |
                              # | 4 |
        4: [c0, c1, c2],      # | | |
                              # | | 3
        3: [c0, c1, c2],      # | |/
                              # 2 |
        2: [c0, c1],          # | |
                              # | 1
        1: [c0, c1],          # |/
                              # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def test_linecolor_branchfiltered():
    repo = openrepo('named-branch')
    grapher = graph.revision_grapher(repo, {'branch': 'default'})
    c0, c1 = 0, 1
    actualtable = buildlinecolortable(grapher)
    expectedtable = {
                      # 7
        7: [c0],      # |
                      # | 6
        6: [c0, c1],  # | |
                      # | 5
        5: [c0, c1],  # | |
                      # | 4
        4: [c0, c1],  # | |
                      # 3 |
        3: [c0, c1],  # |/
                      # 1
        1: [c0],      # |
                      # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def test_linecolor_filelog():
    repo = openrepo('named-branch')
    grapher = graph.filelog_grapher(repo, 'data')
    c0, c1, c2 = 0, 1, 2
    actualtable = buildlinecolortable(grapher)
    expectedtable = {
                          # 7
        7: [c0],          # |
                          # | 6
        6: [c0, c1, c2],  # | |\
                          # | 5 |
        5: [c0, c1, c2],  # | | |
                          # | 4 |
        4: [c0, c1, c2],  # | | |
                          # 3 | |
        3: [c0, c1, c2],  # |/ /
                          # | 2
        2: [c0, c2],      # | |
                          # 1 |
        1: [c0, c2],      # |/
                          # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def setup_20nodes():
    # Graph.index fetches 10 nodes by default
    hg = helpers.HgClient(os.path.join(_tmpdir, '20nodes'))
    hg.init()
    hg.ftouch('data')
    hg.add('data')
    for i in pycompat.xrange(20):
        hg.fappend('data', '%d\n' % i)
        hg.commit('-m', str(i))

def test_graph_index():
    repo = openrepo('20nodes')
    grapher = graph.revision_grapher(repo, {})
    graphobj = graph.Graph(repo, grapher)
    assert_equal(0, len(graphobj))
    assert_equal(0, graphobj.index(None))  # working dir
    assert_equal(1, graphobj.index(19))
    assert_equal(20, graphobj.index(0))
    assert_equal(21, len(graphobj))

    assert_raises(ValueError, lambda: graphobj.index(20))  # unknown

def test_graph_build_0node():
    repo = openrepo('20nodes')
    graphobj = graph.Graph(repo, graph.revision_grapher(repo, {}))
    graphobj.build_nodes(0)
    assert_equal(0, len(graphobj))

def test_graph_build_1node():
    repo = openrepo('20nodes')
    graphobj = graph.Graph(repo, graph.revision_grapher(repo, {}))
    graphobj.build_nodes(1)
    assert_equal(1, len(graphobj))  # [wdir]

def test_graph_build_nodes_up_to_rev():
    repo = openrepo('20nodes')
    graphobj = graph.Graph(repo, graph.revision_grapher(repo, {}))
    graphobj.build_nodes(rev=19)
    assert_equal(2, len(graphobj))  # [wdir, 19]

    graphobj.build_nodes(rev=19)
    assert_equal(2, len(graphobj))

def test_graph_build_nodes_up_to_rev_plus0():
    repo = openrepo('20nodes')
    graphobj = graph.Graph(repo, graph.revision_grapher(repo, {}))
    graphobj.build_nodes(0, 19)
    assert_equal(2, len(graphobj))  # [wdir, 19]

    graphobj.build_nodes(0, 19)
    assert_equal(2, len(graphobj))

def test_graph_build_nodes_up_to_rev_plus1():
    repo = openrepo('20nodes')
    graphobj = graph.Graph(repo, graph.revision_grapher(repo, {}))
    graphobj.build_nodes(1, 19)
    assert_equal(3, len(graphobj))  # [wdir, 19, 18]

    graphobj.build_nodes(1, 18)
    assert_equal(4, len(graphobj))  # [wdir, 19, 18, 17]

def setup_20patches():
    hg = helpers.HgClient(os.path.join(_tmpdir, '20patches'))
    hg.init()
    hg.fappend('data', '0\n')
    hg.commit('-Am', '0')
    hg.fappend('data', '1\n')
    hg.commit('-Am', '1')
    for i in pycompat.xrange(20):
        hg.qnew('%d.diff' % i)
    hg.qpop('-a')

def test_graph_index_unapplied_patches():
    repo = openrepo('20patches')
    grapher = graph.revision_grapher(repo, {})
    graphobj = graph.GraphWithMq(graph.Graph(repo, grapher),
                                 repo.thgmqunappliedpatches)
    assert_equal(20, len(graphobj))  # unapplied-patch nodes are preloaded
    assert_equal(0, graphobj.index('19.diff'))
    assert_equal(19, graphobj.index('0.diff'))
    assert_equal(20, graphobj.index(None))  # working dir
    assert_equal(21, graphobj.index(1))
    assert_equal(22, graphobj.index(0))
    assert_equal(23, len(graphobj))

def setup_nestedbranch():
    buildrepo('nested-branch', r"""
        9
        |\
        | 8 [files=data]
        | 7
        6 |\  [files=data]
        | | 5 [files=data]
        | 4 | [files=data]
        | | 3 [files=data]
        | |/
        2 | [files=data]
        | 1 [files=data]
        |/
        0 [files=data]
    """)

def test_linecolor_nestedbranch():
    repo = openrepo('nested-branch')
    grapher = graph.revision_grapher(repo, {})
    c0, c1, c2 = 0, 1, 2
    actualtable = buildlinecolortable(grapher)
    expectedtable = {
                              # wt
        None: [c0],           # |
                              # 9
        9: [c0, c1],          # |\
                              # | 8
        8: [c0, c1],          # | |
                              # | 7
        7: [c0, c1, c2],      # | |\
                              # 6 | |
        6: [c0, c1, c2],      # | | |
                              # | | 5
        5: [c0, c1, c2],      # | | |
                              # | 4 |
        4: [c0, c1, c2],      # | | |
                              # | | 3
        3: [c0, c1, c2],      # | |/
                              # 2 |
        2: [c0, c1],          # | |
                              # | 1
        1: [c0, c1],          # |/
                              # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def test_linecolor_filelog_nestedbranch():
    repo = openrepo('nested-branch')
    grapher = graph.filelog_grapher(repo, 'data')
    c0, c1, c2 = 0, 1, 2
    actualtable = buildlinecolortable(grapher)
    expectedtable = {
                              # 9
        9: [c0, c1],          # |\
                              # | 8
        8: [c0, c1],          # | |
                              # | 7
        7: [c0, c1, c2],      # | |\
                              # 6 | |
        6: [c0, c1, c2],      # | | |
                              # | | 5
        5: [c0, c1, c2],      # | | |
                              # | 4 |
        4: [c0, c1, c2],      # | | |
                              # | | 3
        3: [c0, c1, c2],      # | |/
                              # 2 |
        2: [c0, c1],          # | |
                              # | 1
        1: [c0, c1],          # |/
                              # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def setup_straightenedbyrevset():
    buildrepo('straightened-by-revset', r"""
        7
        6
        |\
        5 |
        | 4
        3 |
        | 2
        |/
        1
        0
    """)

def test_linecolor_straightened_by_revset():
    repo = openrepo('straightened-by-revset')
    revset = {0, 1, 2, 4, 6, 7}  # exclude 3, 5
    grapher = graph.revision_grapher(repo, {"revset": revset})
    c0, c1 = 0, 1
    actualtable = buildlinecolortable(grapher)
    expectedtable = {
                              # 7
        7: [c0],              # |
                              # 6
        6: [c1],              #  \
                              #   4
        4: [c1],              #   |
                              #   2
        2: [c1],              #  /
                              # 1
        1: [c0],              # |
                              # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def test_linecolor_straightened_by_revset_2():
    repo = openrepo('straightened-by-revset')
    revset = {0, 1, 2, 3, 4, 6, 7}  # exclude 5
    grapher = graph.revision_grapher(repo, {"revset": revset})
    c0, c1 = 0, 1
    actualtable = buildlinecolortable(grapher)
    expectedtable = {
                              # 7
        7: [c0],              # |
                              # 6
        6: [c1],              # |
                              # 4
        4: [c1],              # |
                              # | 3
        3: [c1, c0],          # | |
                              # 2 |
        2: [c1, c0],          # |/
                              # 1
        1: [c0],              # |
                              # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def test_linecolor_straightened_by_revset_3():
    repo = openrepo('straightened-by-revset')
    revset = {0, 1, 2, 3, 6, 7}  # exclude 4, 5
    grapher = graph.revision_grapher(repo, {"revset": revset})
    c0, c1 = 0, 1
    actualtable = buildlinecolortable(grapher)
    expectedtable = {
                              # 7
        7: [c0],              # |
                              # 6
        6: [],                #
                              # 3
        3: [c0],              # |
                              # | 2
        2: [c0, c1],          # |/
                              # 1
        1: [c0],              # |
                              # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def test_linecolor_straightened_by_revset_4():
    repo = openrepo('straightened-by-revset')
    revset = {0, 1, 3, 4, 6, 7}  # exclude 2, 5
    grapher = graph.revision_grapher(repo, {"revset": revset})
    c0, c1 = 0, 1
    actualtable = buildlinecolortable(grapher)
    expectedtable = {
                              # 7
        7: [c0],              # |
                              # 6
        6: [c1],              #  \
                              #   4
        4: [],                #
                              # 3
        3: [c0],              # |
                              # 1
        1: [c0],              # |
                              # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def setup_bulkgraft():
    buildrepo('bulkgraft', r"""
    7 [source=3]
    6 [source=2]
    5 [source=1]
    4
    | 3
    | 2 [branch=foo]
    | 1
    |/
    0
    """)

def test_linecolor_bulkgraft():
    repo = openrepo('bulkgraft')
    grapher = graph.revision_grapher(repo, {"showgraftsource": True})
    c0, c1, c2, c3, c4 = 0, 1, 2, 3, 4
    actualtable = buildlinecolortable(grapher)
    expectedtable = {
                                # wt
        None: [c0],             # |
                                # 7
        7: [c0, c1],            # |\
                                # 6 .
        6: [c0, c2, c1],        # |\ \
                                # 5 . .
        5: [c0, c3, c2, c1],    # |\ \ \
                                # 4 : : :
        4: [c0, c3, c2, c1],    # | : : :
                                # | : : 3
        3: [c0, c3, c2, c4],    # | : :/
                                # | : 2
        2: [c0, c3, c4],        # | :/
                                # | 1
        1: [c0, c4],            # |/
                                # 0
        0: [],
    }
    assert_equal(expectedtable, actualtable)

def setup_commonedge():
    buildrepo('commonedge', r"""
        6
        | 5
        |/
        | 4
        |/
        | 3
        | |
        | 2
        |/
        1
        |
        0
    """)

def test_linecolor_commonedge():
    repo = openrepo('commonedge')
    grapher = graph.revision_grapher(repo, {})
    c0, c1, c2, c3 = 0, 1, 2, 3
    actualtable = buildlinecolortable(grapher)
    expectedtable = {       # wt
        None: [c0],         # |
                            # 6
        6: [c0],            # |
                            # | 5
        5: [c0, c1],        # |/
                            # | 4
        4: [c0, c2],        # |/
                            # | 3
        3: [c0, c3],        # | |
                            # | 2
        2: [c0, c3],        # |/
                            # 1
        1: [c0],            # |
                            # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def setup_manyheads():
    buildrepo('manyheads', r"""
    8
    |\  7
    | | 6
    | |/
    | 5 [branch=foo]
    |/| 4 [branch=foo]
    3 |/
    | 2
    |/
    1
    0
    """)

def test_grapher_noopt():
    repo = openrepo('manyheads')
    grapher = graph.revision_grapher(repo, {})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                                        # wt
        None : ['0-0'],                 # |
                                        # 8
        8 : ['0-0', '0-1'],             # |\
                                        # | | 7
        7 : ['0-0', '1-1', '2-2'],      # | | |
                                        # | | 6
        6 : ['0-0', '1-1', '2-1'],      # | |/
                                        # | 5
        5 : ['0-0', '1-0', '1-1'],      # |/|
                                        # | | 4
        4 : ['0-0', '1-1', '2-1'],      # | |/
                                        # 3 |
        3 : ['0-0', '1-1'],             # | |
                                        # | 2
        2 : ['0-0', '1-0'],             # |/
                                        # 1
        1 : ['0-0'],                    # |
                                        # 0
        0 : [],
        }
    assert_equal(expectedtable, actualtable)

def test_grapher_branch_1():
    repo = openrepo('manyheads')
    grapher = graph.revision_grapher(repo, {'branch': 'default'})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                                # wt
        None: ['0-0'],          # |
                                # 8
        8: ['0-0'],             # |
                                # 3
        3: ['0-0'],             # |
                                # | 2
        2: ['0-0', '1-0'],      # |/
                                # 1
        1: ['0-0'],             # |
                                # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def test_grapher_branch_2():
    repo = openrepo('manyheads')
    grapher = graph.revision_grapher(repo, {'branch': 'foo'})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                        # 7
        7 :['0-0'],     # |
                        # 6
        6 :['0-0'],     # |
                        # 5
        5 :[],          #
                        # 4
        4 :[],          #
        }
    assert_equal(expectedtable, actualtable)

def test_grapher_branch_allparents_1():
    repo = openrepo('manyheads')
    grapher = graph.revision_grapher(
            repo, {'branch': 'default', 'allparents': True})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                                     # wt
        None: ['0-0'],               # |
                                     # 8
        8: ['0-0', '0-1'],           # |\
                                     # | 5
        5: ['0-0', '1-0', '1-1'],    # |/|
                                     # 3 |
        3: ['0-0', '1-1'],           # | |
                                     # | 2
        2: ['0-0', '1-0'],           # |/
                                     # 1
        1: ['0-0'],                  # |
                                     # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def test_grapher_branch_allparents_2():
    repo = openrepo('manyheads')
    grapher = graph.revision_grapher(
            repo, {'branch': 'foo', 'allparents': True})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                                     # 7
        7: ['0-0'],                  # |
                                     # 6
        6: ['0-0'],                  # |
                                     # 5
        5: ['0-0', '0-1'],           # |\
                                     # +---4
        4: ['0-0', '1-1', '2-0'],    # | |
                                     # | 3
        3: ['0-0', '1-1'],           # | |
                                     # 2 |
        2: ['0-0', '1-0'],           # |/
                                     # 1
        1: ['0-0'],                  # |
                                     # 0
        0: [],
        }
    assert_equal(expectedtable, actualtable)

def test_grapher_revset_1():
    repo = openrepo('manyheads')
    revset = {8, 6, 5, 4, 3}
    grapher = graph.revision_grapher(repo, {'revset': revset})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                                    # 8
        8: ['0-0', '0-1'],          # |\
                                    # | | 6
        6: ['0-0', '1-1', '2-1'],   # | |/
                                    # | 5
        5: ['0-0', '1-0'],          # |/
                                    # | 4
        4: ['0-0'],                 # |
                                    # 3
        3: [],
        }
    assert_equal(expectedtable, actualtable)

def test_grapher_revset_2():
    repo = openrepo('manyheads')
    revset = {5, 4, 3, 2, 1}
    grapher = graph.revision_grapher(repo, {'revset': revset})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                                    # 5
        5: ['0-0', '0-1'],          # |\
                                    # +---4
        4: ['0-0', '1-1', '2-0'],   # | |
                                    # | 3
        3: ['0-0', '1-1'],          # | |
                                    # 2 |
        2: ['0-0', '1-0'],          # |/
                                    # 1
        1: [],
        }
    assert_equal(expectedtable, actualtable)

def test_grapher_revset_3():
    repo = openrepo('manyheads')
    revset = {8, 5, 3}
    grapher = graph.revision_grapher(repo, {'revset': revset})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                                    # 8
        8: ['0-0', '0-1'],          # |\
                                    # | 5
        5: ['0-0', '1-0'],          # |/
                                    # 3
        3: [],                      #
        }
    assert_equal(expectedtable, actualtable)

def test_grapher_showgraftsource():
    repo = openrepo('bulkgraft')
    grapher = graph.revision_grapher(repo, {"showgraftsource": True})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                                            # wt
        None: ['0-0'],                      # |
                                            # 7
        7: ['0-0', '0-1G'],                 # |\
                                            # 6 .
        6: ['0-0', '0-1G', '1-2G'],         # |\ \
                                            # 5 . .
        5: ['0-0', '0-1G', '1-2G', '2-3G'], # |\ \ \
                                            # 4 : : :
        4: ['0-0', '1-1G', '2-2G', '3-3G'], # | : : :
                                            # | : : 3
        3: ['0-0', '1-1G', '2-2G', '3-2'],  # | : :/
                                            # | : 2
        2: ['0-0', '1-1G', '2-1'],          # | :/
                                            # | 1
        1: ['0-0', '1-0'],                  # |/
                                            # 0
        0: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_showgraftsource_with_branch():
    repo = openrepo('bulkgraft')
    grapher = graph.revision_grapher(
        repo, {"showgraftsource": True, "branch": "default"})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                            # wt
        None: ['0-0'],      # |
                            # 7
        7: ['0-0'],         # |
                            # 6
        6: ['0-0'],         # |
                            # 5
        5: ['0-0', '0-1G'], # |\
                            # 4 :
        4: ['0-0', '1-1G'], # | :
                            # | 1
        1: ['0-0', '1-0'],  # |/
                            # 0
        0: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_hidegraftsource():
    repo = openrepo('bulkgraft')
    grapher = graph.revision_grapher(repo, {})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                            # wt
        None: ['0-0'],      # |
                            # 7
        7: ['0-0'],         # |
                            # 6
        6: ['0-0'],         # |
                            # 5
        5: ['0-0'],         # |
                            # 4
        4: ['0-0'],         # |
                            # | 3
        3: ['0-0', '1-1'],  # | |
                            # | 2
        2: ['0-0', '1-1'],  # | |
                            # | 1
        1: ['0-0', '1-0'],  # |/
                            # 0
        0: [],
    }
    assert_equal(expectedtable, actualtable)

def setup_obsolete():
    buildrepo('obsolete', r"""
    2 [precs=1]
    | 1
    |/
    0
    """)

def test_grapher_hiddenrev():
    repo = openrepo('obsolete')
    grapher = graph.revision_grapher(repo, {})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                            # wt
        None: ['0-0'],      # |
                            # 2
        2: ['0-0'],         # |
                            # 0
        0: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_showobsolete():
    repo = openrepo('obsolete').unfiltered()
    grapher = graph.revision_grapher(repo, {'showgraftsource': True})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
                            # wt
        None: ['0-0'],      # |
                            # 2
        2: ['0-0', '0-1O'], # |`
                            # | 1
        1: ['0-0', '1-0'],  # |/
                            # 0
        0: [],
    }
    assert_equal(expectedtable, actualtable)

def setup_familyline():
    buildrepo('familyline', r"""
    o        # 12
    |\    o  # 11
    o---+ |  # 10
    | 9 |/
    |/| 8
    | 7 |
    6 |\|
    |\| 5
    | 4 |
    |/| 3
    2 |/
    | 1 [branch=foo]
    |/
    0
    """)

def test_grapher_familyline_islands():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {12, 11}})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
        12: [],
        11: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_1_parent():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {12, 10}})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
        12: ['0-0'],
        10: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_2_parents():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {9, 7, 6}})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {       # 9
        9: ['0-0', '0-1'],  # |\
                            # 7 |
        7: ['1-0'],         #  /
                            # 6
        6: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_1_nva():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {9, 4}})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
        9: ['0-0F'],
        4: []
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_2_nvas():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {7, 3, 2}})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {         # 7
        7: ['0-0F', '0-1F'],  # |\
                              # | 3
        3: ['0-0F'],          # |
                              # 2    2 is treated as 1st parent because
        2: [],                #      it is ancestor of 4(1st parent of 7)
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_simple_case_1():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {7, 4, 3, 1}})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {         # 7
        7: ['0-0', '0-1F'],   # |\
                              # 4 |
        4: ['0-0', '1-1F'],   # | |
                              # | 3
        3: ['0-0', '1-0'],    # |/
                              # 1
        1: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_simple_case_2():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {7, 5, 4, 1}})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {         # 7
        7: ['0-0', '0-1'],    # |\
                              # | 5
        5: ['0-0', '1-1F'],   # | |
                              # 4 |
        4: ['0-0', '1-0F'],   # |/
                              # 1
        1: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_many_parents():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {12, 11, 8, 7, 6}})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {                           # 12--+
        12: ['0-0F', '0-1F', '0-2F'],           # |\  |
                                                # | +---11
        11: ['0-0F', '1-1F', '2-2F', '3-1'],    # | | |
                                                # | 8 |
         8: ['0-0F', '2-1F'],                   # |  /
                                                # | 7
         7: ['0-0F'],                           # |
                                                # 6
         6: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_dont_draw_familyline_to_parent():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {6, 2}})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {         # 6
        6: ['0-0'],           # | familyline between 6 and 2 (from 6-4-2) is
                              # 2 not drawn because 2 is direct parent of 6
        2: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_dont_draw_familyline_to_ancestor_of_visible_p1():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {9, 7, 2}})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {         # 9
        9: ['0-0'],           # | familyline between 9 and 2 (from 9-6-2) is
                              # 7 not drawn because 2 is ancestor of 7
        7: ['0-0F'],          # |
                              # 2
        2: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_dont_draw_familyline_to_ancestor_of_visible_p2():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {9, 6, 1}})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {         # 9
        9: ['0-0'],           # | familyline between 9 and 2 (from 9-7-2) is
                              # 6 not drawn because 2 is ancestor of 6
        6: ['0-0F'],          # |
                              # 1
        1: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_dont_draw_familyline_to_ancestor_of_other_nva():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {9, 5, 1}})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {         # 9
        9: ['0-0F'],          # | familyline between 9 and 1 (from 9-7-4-1) is
                              # 5 not drawn because 1 is ancestor of 5
        5: ['0-0F'],          # |
                              # 1
        1: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_branch():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {10, 9, 8, 6, 5},
                                            'branch': 'foo'})
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {         # 9
        9: ['0-0F'],          # |
                              # | 8
        8: ['0-0F', '1-0'],   # |/
                              # 5
        5: [],
    }
    assert_equal(expectedtable, actualtable)

def test_grapher_familyline_invisible_earliest():
    repo = openrepo('familyline')
    grapher = graph.revision_grapher(repo, {'showfamilyline': True,
                                            'revset': {1, 0},
                                            'branch': 'foo'})
    # should empty queue even if the earliest revision is invisible
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
        1: [],
    }
    assert_equal(expectedtable, actualtable)

def setup_movedfile():
    buildrepo('movedfile', r"""
    6 [files="baz"] # add baz again
    5
    4 [files="foo2=>foo3, bar=>, baz=>"]
    3 [files="foo2"]
    2 [files="foo=>foo2, bar, baz"]
    1
    0 [files="foo, bar, baz"]
    """)

def buildpathtable(grapher):
    return dict((n.rev, n.extra[0]) for n in grapher)

def test_filelog_movedpath():
    repo = openrepo('movedfile')
    grapher = graph.filelog_grapher(repo, 'foo3')
    assert_equal({4: 'foo3', 3: 'foo2', 2: 'foo2', 0: 'foo'},
                 buildpathtable(grapher))

def test_filelog_removedpath():
    repo = openrepo('movedfile')
    grapher = graph.filelog_grapher(repo, 'bar')
    assert_equal({2: 'bar', 0: 'bar'},
                 buildpathtable(grapher))

def test_filelog_readdedpath():
    repo = openrepo('movedfile')
    grapher = graph.filelog_grapher(repo, 'baz')
    assert_equal({6: 'baz', 2: 'baz', 0: 'baz'},
                 buildpathtable(grapher))

def test_filelog_readded_file():
    repo = openrepo('movedfile')
    grapher = graph.filelog_grapher(repo, 'baz')
    actualtable = buildlinecolumntable(grapher)
    expectedtable = {
        6: [],      # 6
                    #
        2: ['0-0'], # 2
                    # |
        0: [],      # 0
    }
    assert_equal(expectedtable, actualtable)
