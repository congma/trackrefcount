from unittest import TestCase
from trackrefcount import TrackRCFor, Pos, Neg, NonNeg, NonPos, Anything


class TestRefCountTracker(TestCase):
    def test_empty_body(self):
        a = object()
        b = object()
        with TrackRCFor(a, b) as t:
            pass
        t.assertEqualRC()

    def test_empty_args(self):
        with TrackRCFor() as t:
            k = 1
        t.assertEqualRC()

    def test_empty_empty(self):
        with TrackRCFor() as t:
            pass
        t.assertEqualRC()

    def test_anonymous_expression(self):
        with TrackRCFor([1]) as t:
            pass
        t.assertEqualRC()

    def test_bind_to_context_manager_args(self):
        with TrackRCFor([1]) as t:
            a = t.args[0]
        t.assertDelta(1)

    def test_repeated_args(self):
        a = "spam, spam, spam, spam"
        with TrackRCFor(a, a, a) as t:
            del a
        t.assertDelta(-1, -1, -1)

    def test_just_one_arg_in_delta_check(self):
        a, b, c = "spam", "spammer", "spamming"
        with TrackRCFor(a, b, c) as t:
            s = (a, b, c)
        t.assertDelta(1)

    def test_bare_expression_as_statement(self):
        thing = "abc"
        with TrackRCFor(thing) as k:
            thing
        k.assertEqualRC()

    def test_increase_refcount_by_binding_new_name(self):
        thing = 0
        with TrackRCFor(thing) as k:
            anotherthing = thing
        k.assertDelta(1)

    def test_decrease_refcount_by_del(self):
        class K:
            pass
        cls = K
        with TrackRCFor(K) as keeper:
            del K
        keeper.assertDelta(-1)

    def test_container(self):
        thing = dict.__getitem__
        with TrackRCFor(thing) as k:
            box = [thing]
        k.assertDelta(1)

    def test_attribute(self):
        class K:
            def __init__(self, other):
                self.attr = other
        k = K("spam")
        with TrackRCFor(k.attr) as t:
            del k.attr
        t.assertDelta(-1)

    def test_raise_exception(self):
        class SomeException(Exception):
            pass

        def just_raise(arg):
            raise SomeException(arg)

        k = "An argument"
        with TrackRCFor(k, SomeException) as t:
            try:
                m = just_raise(k)
            except SomeException as exc:
                pass
        t.assertEqualRC()

    def test_scope(self):
        k = "Something in the outer scope"
        def f():
            nonlocal k
            with TrackRCFor(k) as t:
                d = dict(key=k)
            # <---
            # ^ This is where the context manager exits. It essentially saves
            # the context regarding refcounts *before* the name "d" goes out of
            # scope as f returns.
            return t
        tracker = f()
        # Here the context manager has exited and shouldn't be affected by
        # further manipulation on k.
        del k
        tracker.assertDelta(1)

    def test_assert_before_exiting(self):
        a = object(); b = object()
        with self.assertRaisesRegex(TypeError, "Context has not finalized"):
            with TrackRCFor(a, b) as t:
                c = a
                t.assertDelta(1, 0)

    def test_nested_context_managers(self):
        a, b = "vegan spam", "eggs"
        with TrackRCFor(a) as outer:
            d = dict(buy=a, sell=b)
            with TrackRCFor(a, b) as inner:
                del d["buy"]
            inner.assertDelta(-1, 0)
            del d
        outer.assertEqualRC()

    def test_nesting_by_self_duplication(self):
        a, b = "cucumber", "pepper"
        with TrackRCFor(a, b) as f:
            d = dict(buy=a, sell=b)
            with f() as g:
                d.pop("sell")
            self.assertIsNot(g, f)
            g.assertDelta(0, -1)
            del d
        f.assertEqualRC()

    def test_nesting_by_using_pre_instantiated(self):
        a = "Another Python string, given to name \"a\""
        inner = TrackRCFor(a)
        # "outer" will see "a" decrefed twice, first by the del statement, then
        # by deleting "inner" (which itself holds a reference to a).
        with TrackRCFor(inner, a) as outer:
            with inner:
                del a
            inner.assertDelta(-1)
            del inner
        outer.assertDelta(-1, -2)

    def test_ref_cycle(self):
        a = []; b = []; c = []
        with TrackRCFor(a, b, c) as t:
            a.append(b); b.append(c); c.append(a)
            del a, b, c
        t.assertEqualRC()

    def test_reuse_fail(self):
        a = object()
        with TrackRCFor(a) as t:
            pass
        with self.assertRaisesRegex(TypeError, "Context expired"):
            with t:
                pass

    def test_wrong_arglist_length(self):
        a = object()
        b = object()
        with TrackRCFor(a, b) as t:
            pass
        with self.assertRaisesRegex(ValueError,
                                    "Length of argument-lists mismatch"):
            t.assertDelta(0, 0, 0)

    def test_separation_of_init_and_enter(self):
        a = object()
        t = TrackRCFor(a)
        c = a
        with t:
            del c
            del a
        t.assertDelta(-2)

    def test_bad_assert(self):
        a = object()
        with self.assertRaises(AssertionError):
            with TrackRCFor(a) as t:
                del a
            t.assertEqualRC()


class TestUsingPseudoNums(TestCase):
    """Test the use of pseudo-numbers as substitute for exact delta values.
    """
    def test_use_pos(self):
        a = object()
        with TrackRCFor(a) as t:
            b = a
        t.assertDelta(Pos)

    def test_use_nonpos(self):
        a = object()
        with TrackRCFor(a) as t:
            del a
        t.assertDelta(Neg)

    def test_use_anything(self):
        a = object(); b = object()
        with TrackRCFor(a, b) as t:
            a = b
        t.assertDelta(Anything)

    def test_use_mixed(self):
        a = object(); b = object(); c = object()
        with TrackRCFor(a, b, c) as t:
            a = b
            del c
        t.assertDelta(Neg, Pos, NonPos)

    def test_use_with_number(self):
        a = object(); b = object(); c = "spam"
        with TrackRCFor(a, b, c) as t:
            d = a
            b = {c: c}
        t.assertDelta(1, Neg, NonNeg)
