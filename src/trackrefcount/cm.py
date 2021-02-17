from sys import getrefcount
from typing import Sequence, List, ContextManager
from contextlib import AbstractContextManager


def rc(args: Sequence) -> List[int]:
    """Return a list of reference counts reported by sys.getrefcount for each
    element in args.
    """
    # Using list comprehension will add the value by one due to intermediate
    # variable (unless explicitly suppressed). This doesn't matter -- just FYI.
    return list(map(getrefcount, args))


class TrackRCFor(AbstractContextManager):
    """Track the reference count for a sequence of objects specified as
    arguments at init time.
    """
    def __init__(self, *args) -> None:
        """Create a context manager that can be entered later by specifying
        which variables/names to track.
        """
        self.args = args
        self.n = len(args)
        self.c_initial = None
        self.c_final = None
        self.exited = False

    def __call__(self) -> ContextManager:
        """Called with no arguments: return a duplicate of self."""
        return self.__class__(*self.args)

    def __enter__(self) -> ContextManager:
        try:
            args = self.args
        except AttributeError:
            raise TypeError("Context expired")
        self.c_initial = rc(args)
        return self

    def __exit__(self, *exc_args) -> bool:
        self.c_final = rc(self.args)
        del self.args  # Make it nicer to work with nested contexts.
        self.exited = True
        return False

    def assertDelta(self, *assumptions) -> None:
        """Assert the difference(s) in refcount ("after" minus "before") is the
        assumed amount.
        """
        if not self.exited:
            raise TypeError("Context has not finalized")
        deltas = [a - b for a, b in zip(self.c_final, self.c_initial)]
        if len(assumptions) == 1:
            assumed = [assumptions[0]] * self.n
        else:
            assumed = list(assumptions)
        if len(assumed) != len(deltas):
            raise ValueError("Length of argument-lists mismatch")
        assert deltas == assumed

    def assertEqualRC(self) -> None:
        """Shorthand for asserting no change in refcount."""
        self.assertDelta(0)
