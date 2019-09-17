import re
from nose.tools import *
from tortoisehg.hgqt import graph

P = graph.LINE_TYPE_PARENT
F = graph.LINE_TYPE_FAMILY

def revs(revstring):
    """
    generate _FamilyLineRev instances acording to specified text

    '1'    -> _FamilyLineRev(1, True)
    '1x'   -> _FamilyLineRev(1, False)
    '2, 1x' -> _FamilyLineRev(2, True), _FamilyLineRev(1, False)
    """
    keyexp = re.compile(r'^\s*(\d+)(x?)\s*$')
    for rev in revstring.split(','):
        m = keyexp.match(rev)
        if m:
            yield graph._FamilyLineRev(int(m.group(1)), not m.group(2))
        else:
            raise ValueError(rev)

def assert_rev(rev, pending, dests):
    eq_(pending, rev.pending)
    eq_(set(dests), set(rev.destinations))

class TestPendingAfterFixingItself(object):
    """
    Test value of _FamilyLineRev.pending after proceed() called
    """
    def test_no_parents(self):
        r0, = revs('0')
        r0.proceed([])
        # rev with no parents is finished immidiately
        assert_rev(r0, pending=0, dests=[])

    def test_1_visible_parent(self):
        r9, r8 = revs('9, 8')
        r9.proceed([r8])
        # rev with 1 visible parent is finished immidiately
        assert_rev(r9, pending=0, dests=[(8, P, True)])

    def test_2_visible_parents(self):
        r9, r8, r7 = revs('9, 8, 7')
        r9.proceed([r8, r7])
        # rev with 1 visible parent is finished immidiately
        assert_rev(r9, pending=0, dests=[(8, P, True), (7, P, False)])

    def test_1_hidden_parent(self):
        r9, x8 = revs('9, 8x')
        r9.proceed([x8])
        assert_rev(r9, pending=1, dests=[])

    def test_2_hidden_parents(self):
        r9, x8, x7 = revs('9, 8x, 7x')
        r9.proceed([x8, x7])
        assert_rev(r9, pending=2, dests=[])

    def test_visible_and_hidden_parents(self):
        r9, r8, x7 = revs('9, 8, 7x')
        r9.proceed([r8, x7])
        assert_rev(r9, pending=1, dests=[(8, P, True)])

    def test_hidden_and_visible_parents(self):
        r9, x8, r7 = revs('9, 8x, 7')
        r9.proceed([x8, r7])
        assert_rev(r9, pending=1, dests=[(7, P, False)])


class TestPendingAfterFixingParent(object):
    """
    Test value of _FamilyLineRev.pending after proceed() called against its
    parent
    """
    def test_no_grandparent(self):
        r1, x0 = revs('1, 0x')
        r1.proceed([x0])
        x0.proceed([])
        assert_rev(r1, pending=0, dests=[])

    def test_1_visible_grandparent(self):
        r9, x8, r7, r6 = revs('9, 8x, 7, 6')
        r9.proceed([x8])
        x8.proceed([r7])
        assert_rev(r9, pending=1, dests=[])
        r7.proceed([r6])
        assert_rev(r9, pending=0, dests=[(7, F, True)])

    def test_2_visible_grandparents(self):
        r9, x8, r7, r6, r5 = revs('9, 8x, 7, 6, 5')
        r9.proceed([x8])
        assert_rev(r9, pending=1, dests=[])
        x8.proceed([r7, r6])
        assert_rev(r9, pending=2, dests=[])
        r7.proceed([r5])
        assert_rev(r9, pending=1, dests=[(7, F, True)])
        r6.proceed([r5])
        assert_rev(r9, pending=0, dests=[(7, F, True), (6, F, True)])

    def test_1_hidden_grandparent(self):
        r9, x8, x7, r6, x5 = revs('9, 8x,  7x, 6, 5x')
        r9.proceed([x8])
        assert_rev(r9, pending=1, dests=[])
        x8.proceed([x7])
        assert_rev(r9, pending=1, dests=[])
        x7.proceed([r6])
        assert_rev(r9, pending=1, dests=[])
        r6.proceed([x5])
        assert_rev(r9, pending=0, dests=[(6, F, True)])

    def test_visible_and_hidden_grandparents(self):
        r9, x8, r7, x6, x5 = revs('9, 8x, 7, 6x, 5x')
        r9.proceed([x8])
        assert_rev(r9, pending=1, dests=[])
        x8.proceed([r7, x6])
        assert_rev(r9, pending=2, dests=[])
        r7.proceed([x5])
        eq_(r9.pending, 1) # 6
        assert_rev(r9, pending=1, dests=[(7, F, True)])
        x6.proceed([x5])
        assert_rev(r9, pending=1, dests=[(7, F, True)])

    def test_duplicated_grandparent(self):
        r9, x8, x7, x6, x5, x4 = revs('9, 8x, 7x, 6x, 5x, 4x')
        r9.proceed([x8, x7])
        assert_rev(r9, pending=2, dests=[]) # 8, 7 are still pending
        x8.proceed([x6, x5])
        assert_rev(r9, pending=3, dests=[]) # 7, 6, 5
        x7.proceed([x6, x4])
        assert_rev(r9, pending=3, dests=[]) # 6, 5, 4 / don't count 6 twice

class TestIgnoredNVAs(object):
    """
    Test behaviour about omitting duplicated edge
    """
    def test_nva_is_parent(self):
        # 9
        # |\
        # | 8x
        # |/
        # 7
        r9, x8, r7, r6 = revs('9, 8x, 7, 6')
        r9.proceed([r7, x8])
        x8.proceed([r7])
        r7.proceed([r6])
        assert_rev(r9, pending=0, dests=[(7, P, True)])

    def test_nva_is_parent_of_visible_parent(self):
        # 9
        # |\
        # | 8x
        # 7 |
        # |/
        # 6
        r9, x8, r7, r6, r5 = revs('9, 8x, 7, 6, 5')
        r9.proceed([r7, x8])
        x8.proceed([r6])
        r7.proceed([r6])
        r6.proceed([r5])
        # 6 is not nva of 9 because it is parent of 7
        assert_rev(r9, pending=0, dests=[(7, P, True)])

    def test_nva_is_parent_of_other_nva(self):
        # 9
        # |\
        # | 8x
        # 7x|
        # | |
        # 6 |
        # |/|
        # 5 |
        # |/
        # 4
        r9, x8, x7, r6, r5, r4, r3 = revs('9, 8x, 7x, 6, 5, 4, 3')
        r9.proceed([x7, x8])
        x8.proceed([r5, r4])
        x7.proceed([r6])
        r6.proceed([r5])
        r5.proceed([r4])
        r4.proceed([r3])
        eq_(r9.pending, 0)
        # 5 is excluded because it is parent of 6
        # and 4 is excluded because it is parent of 5
        assert_rev(r9, pending=0, dests=[(6, F, True)])

class TestP1OrNot(object):
    """
    Test is_p1 value of each NVAs
    """
    def test_both_parents_visible_1(self):
        # 9
        # |\
        # 8 |
        # | 7
        r9, r8, r7 = revs('9, 8, 7')
        r9.proceed([r8, r7])
        assert_rev(r9, pending=0, dests=[(8, P, True), (7, P, False)])

    def test_both_parents_visible_2(self):
        # 9
        # |\
        # | 8
        # 7 |
        r9, r8, r7 = revs('9, 8, 7')
        r9.proceed([r7, r8])
        assert_rev(r9, pending=0, dests=[(7, P, True), (8, P, False)])

    def test_p1_visible_p2_hidden(self):
        # 9
        # |\
        # 8 |
        # | 7x
        # | 6
        # |/
        # 5
        r9, r8, x7, r6, r5 = revs('9, 8, 7x, 6, 5')
        r9.proceed([r8, x7])
        r8.proceed([r5])
        x7.proceed([r6])
        r6.proceed([r5])
        assert_rev(r9, pending=0, dests=[(8, P, True), (6, F, False)])

    def test_p1_hidden_p2_visible(self):
        # 9
        # |\
        # 8x|
        # | 7
        # 6 |
        # |/
        # 5
        r9, x8, r7, r6, r5 = revs('9, 8x, 7, 6, 5')
        r9.proceed([x8, r7])
        x8.proceed([r6])
        r7.proceed([r5])
        r6.proceed([r5])
        assert_rev(r9, pending=0, dests=[(6, F, True), (7, P, False)])

    def test_both_hidden(self):
        # 9
        # |\
        # | 8x
        # 7x|
        # | 6
        # 5 |
        # |/
        # 4
        r9, x8, x7, r6, r5, r4 = revs('9, 8x, 7x, 6, 5, 4')
        r9.proceed([x7, x8])
        x8.proceed([r6])
        x7.proceed([r5])
        r6.proceed([r4])
        r5.proceed([r4])
        assert_rev(r9, pending=0, dests=[(5, F, True), (6, F, False)])

    def test_both_parents_have_same_nva_1(self):
        # 9
        # |\
        # | 8x
        # 7x|
        # |/
        # 6
        r9, x8, x7, r6, r5 = revs('9, 8x, 7x, 6, 5')
        r9.proceed([x7, x8])
        x8.proceed([r6])
        x7.proceed([r6])
        r6.proceed([r5])
        assert_rev(r9, pending=0, dests=[(6, F, True)])

    def test_both_parents_have_same_nva_2(self):
        # 9
        # |\
        # 8x|
        # | 7x
        # |/
        # 6
        r9, x8, x7, r6, r5 = revs('9, 8x, 7x, 6, 5')
        r9.proceed([x8, x7])
        x8.proceed([r6])
        x7.proceed([r6])
        r6.proceed([r5])
        assert_rev(r9, pending=0, dests=[(6, F, True)])
