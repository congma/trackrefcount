from unittest import TestCase
import pytest
from trackrefcount import Pos, Neg, NonPos, NonNeg, Anything


class TestIs:
    """Test the "is" operator"""
    def test_isneg(self):
        assert Pos is -Neg
        assert Neg is -Pos
        assert NonNeg is -NonPos
        assert NonPos is -NonNeg

    @pytest.mark.parametrize("x", [Pos, Neg, NonPos, NonNeg])
    def test_ispos(self, x):
        assert x is +x

    @pytest.mark.parametrize("x", [Pos, Neg, NonPos, NonNeg])
    def test_isdoubleneg(self, x):
        assert x is -(-x)

    @pytest.mark.parametrize("x", [Pos, Neg, NonPos, NonNeg])
    def test_isdoubleinv(self, x):
        assert x is ~(~x)

    def test_isnot(self):
        assert Pos is not Neg
        assert Neg is not Pos

    @pytest.mark.parametrize("x", [Pos, Neg, Anything])
    def test_instantiation(self, x):
        assert x is x.__class__()


class TestStrictEquality:
    """Test the == and != operators"""
    @pytest.mark.parametrize("x", [Pos, Neg, NonPos, NonNeg, Anything])
    def test_reflex(self, x):
        assert x == x

    @pytest.mark.parametrize("x", [Pos, Neg, NonPos, NonNeg])
    def test_reflex_double_inv(self, x):
        assert x == ~(~x)

    @pytest.mark.parametrize("x", [Pos, Neg, NonPos, NonNeg])
    def test_reflex_pos(self, x):
        assert x == +x

    @pytest.mark.parametrize("x", [Pos, Neg, NonPos, NonNeg])
    def test_reflex_double_neg(self, x):
        assert x == -(-x)

    @pytest.mark.parametrize("x", [Pos, Neg, NonPos, NonNeg, Anything])
    def test_not_reflex(self, x):
        assert not (x != x)

    @pytest.mark.parametrize("num", range(1, 5))
    def test_pos_eq_number(self, num):
        assert Pos == num
        assert num == Pos

    @pytest.mark.parametrize("num", range(-3, 1))
    def test_pos_neq_number(self, num):
        assert Pos != num
        assert num != Pos

    @pytest.mark.parametrize("num", range(-4, 0))
    def test_neg_eq_number(self, num):
        assert Neg == num
        assert num == Neg

    @pytest.mark.parametrize("num", range(0, 4))
    def test_neg_neq_number(self, num):
        assert Neg != num
        assert num != Neg

    @pytest.mark.parametrize("num", range(0, 4))
    def test_nonneg_eq_number(self, num):
        assert NonNeg == num
        assert num == NonNeg

    @pytest.mark.parametrize("num", range(-4, 0))
    def test_nonneg_neq_number(self, num):
        assert NonNeg != num
        assert num != NonNeg

    @pytest.mark.parametrize("num", range(-3, 1))
    def test_nonpos_eq_number(self, num):
        assert NonPos == num
        assert num == NonPos

    @pytest.mark.parametrize("num", range(1, 5))
    def test_nonpos_neq_number(self, num):
        assert NonPos != num
        assert num != NonPos

    @pytest.mark.parametrize("thing, neg_thing",
                             ((Pos, Neg), (NonPos, NonNeg),
                              (Neg, Pos), (NonNeg, NonPos)))
    def test_inversion(self, thing, neg_thing):
        assert thing == -neg_thing
        assert -thing == neg_thing
        assert -neg_thing == thing
        assert neg_thing == -thing

    @pytest.mark.parametrize("thing", (Pos, Neg, NonPos, NonNeg))
    def test_inversion_neq(self, thing):
        assert thing != -thing
        assert -thing != thing


@pytest.mark.parametrize("thing, thing_repr",
                         ((Pos, "Pos"), (Neg, "Neg"),
                          (NonPos, "NonPos"), (NonNeg, "NonNeg"),
                          (Anything, "Anything")))
class TestRepr:
    def test_repr(self, thing, thing_repr):
        assert ("%r" % thing) == thing_repr


@pytest.mark.parametrize("thing", (Pos, Neg, NonPos, NonNeg, Anything))
def test_unhashable(thing):
    with pytest.raises(TypeError):
        hash(thing)
