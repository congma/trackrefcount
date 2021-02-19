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

    Example:

    >>> a = object(); b = object()
    >>> with TrackRCFor(a, b) as t:
    ...     c = a
    ...     del b
    >>> t.assertDelta(1, -1)

    This is meant to assert that during the "suite" of code in the indented
    block under the "with" statement, the reference count for the object named
    by variable "a" goes up by one (here because of new name-binding to "c"),
    and for "b" it decreases by one (because of the "del" statement). This
    assertion will silently pass because it is true. If the assertion does not
    match the actual change in refcounts, an AssertionError is raised.

    This construct can be used in unit tests for C-extension code on the Python
    side to assert that the reference count changes by a certain amount.

    Although valid Python code changes object refcounts in well-defined ways,
    extension code has much greater leeway and may introduce refcount-breaking
    bugs.
    """
    def __init__(self, *args) -> None:
        """Initialize a context manager that can be entered later by specifying
        which variables/names to track as arguments to the call. The arguments
        to the call are Python objects (loosely "variables") to be tracked by
        the context manager.
        """
        self.args = args
        self.n = len(args)
        self.c_initial = None
        self.c_final = None
        self.exited = False

    def __call__(self) -> ContextManager:
        """Called with no arguments: return a duplicate of self.

        The return value is an instance of the same type that keeps the same
        objects tracked. The new context manager is intended for nested
        contexts, although its use is not restricted to such. Instead of
        re-entering the existing context manager, the preferred way is to
        duplicate and use the new one.

        (These context managers are cheap; duplicating keeps the code's
        intention more apparent. Duplication is not even necessary, because a
        new one can always be created by instantiate from the class directly.
        It is kept as a short hand for creating a new context manager with the
        original tracked objects).

        Example:

        >>> a = object(); b = object()
        >>> with TrackRCFor(a, b) as f:
        ...     c = b
        ...     with f() as g:
        ...         del b
        ...     g.assertDelta(0, -1)
        >>> f.assertEqualRC()
        """
        return self.__class__(*self.args)

    def __enter__(self) -> ContextManager:
        """Enter the managed context by marking the initial refcounts.

        Exited ("expired") context manager cannot be entered again. Doing so
        will raise a TypeError.
        """
        try:
            args = self.args
        except AttributeError:
            raise TypeError("Context expired")
        self.c_initial = rc(args)
        return self

    def __exit__(self, *exc_args) -> bool:
        """Exit the managed context by marking the final refcounts. Exceptions
        raised in the suite (body of the "with"-block) will propagate.
        """
        self.c_final = rc(self.args)
        del self.args  # Make it nicer to work with nested contexts.
        self.exited = True
        return False

    def assertDelta(self, *assumptions) -> None:
        """Assert the difference(s) in refcount ("after" minus "before") is the
        assumed amount.

        The number of positional arguments in "assumptions" must either match
        the number of initially tracked objects, or be one. In the latter case
        it is "broadcast", meaning that the same amout is asserted for each of
        the tracked object. If they don't mach, ValueError will be raised.

        The assertion method cannot be used while the context manager has not
        exited. Doing so will raise TypeError.

        The assertion is made as a normal Python "assert" statement. Normally a
        false assertion will raise AssertionError.
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
        assert deltas == assumed, ("Measured: %r != Asserted: %r" %
                                   (deltas, assumed))

    def assertEqualRC(self) -> None:
        """Shorthand for asserting no change in refcount."""
        self.assertDelta(0)
