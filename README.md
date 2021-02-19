<!--
vim: spell spelllang=en
-->
SYNOPSIS
========

trackrefcount -- Python helper class for tracking reference-count in tests.


SUMMARY
=======

This module provides a context manager class, `TrackRCFor`, that helps with
writing tests that keep track of object reference counts. It is intended for
testing C-extensions, which, unlike pure Python code, have much greater freedom
with manipulating the reference count (or "refcount").

Example:

```python
from trackrefcount import TrackRCFor
a = object(); b = object()
with TrackRCFor(a, b) as f:
    c = b
f.assertDelta(0, 1)
```

In this example:

- The opening `with`-statement expresses the tester's objective to keep track
  of the refcounts for the Python objects referenced by the names (loosely,
  variables) `a` and `b`.
- The code section for which the tracking is in place is the indented block
  under the `with`-statement. In this example, it's just the one line `c = b`.
- The closing statement, after the `with`-block's end, express the tester's
  assertion: that the *changes* to refcounts for `a` and `b` inside the block
  are zero and one, respectively.

For this very simple example, the assertion will pass silently. However, if the
code block contains C-extension code that breaks the normal refcount semantics
explicitly, an `AssertionError` will be raised.


RATIONALE
=========

This simple helper class wraps around Python's `sys.getrefcount` function so
that unit tests can becomes more readable. It is very far from a full-fledged
memory tracer (think: Valgrind), and it cannot detect refcount problems with
*inaccessible* objects kept alive because of incorrect refcounting. It is
supposed to catch the most glaring refcount problems, which typically reflect
underlying issues in the C code.

I explicitly resisted the urge to implement another usage pattern, illustrated
as follows:

```python
with AssertRCFor((a, b), (0, 1)):
   < ... code block under test ... >
# Here, as soon as the context manager exits, the assertion statement is
# automatically executed.
```

I find it easier to write a block of testing code, go over it, and ask myself
"what is the *correct* refcount change?" -- as compared to write down the
asserted amount beforehand. This is unlike the typical pattern with
`unittest` using `assertRaises()`:

```python
with self.assertRaises(SomeError):
    < ... code meant to raise an exception ... >
```

With refcounts we want to test that "nothing strange happens", not "something
strange must happen under certain conditions". Keeping refcounts correct is
unconditional.


MORE USAGE PATTERNS
===================


More on writing an assertion
----------------------------

If the asserted amount of refcount change is the same for all tracked objects,
it suffices to call the `assertDelta()` method with one number as the
argument. As a special case, the `assertEqualRC()` method is exactly the same
as `assertDelta(0)`.


Contexts are cheap
------------------

Asserting using the context manager *inside* the `with`-block is explicitly
disabled. Doing so raises `TypeError`. This context manager is very thin and
cheap, so the recommended way is to just create as many as you need for each
code section you want to test. This also helps narrow down the offending
statement if any.

To save typing, the `TrackRCFor` context manager instance can be easily
duplicated by calling it with no arguments:

```python
a = object(); b = object()
with TrackRCFor(a, b) as f:
    c = b
    with f() as g:  # Duplicate f, track the same objects
        del b
    g.assertDelta(0, -1)
f.assertEqualRC()
```

Duplication means creating a new instance that tracks the same objects.


Matching inexact numbers
------------------------

There could be cases where the exact amount of refcount-change cannot be
conveniently asserted. For this reason the module provides the following
constants or "pseudo-numbers" that can be used in the `assertDelta()` method:

- `Pos`, `Neg`: an unspecified (strictly) positive or negative number;
- `NonNeg`, `NonPos`: an unspecified non-negative or non-positive number;
- `Anything`, matching any number.

These pseudo-numbers cannot do arithmetic or comparison. They can only be used
to *match* actual numbers.


CAVEATS
=======


Reusing doesn't work
--------------------

A `TrackRCFor` context manager instance, if already "exited", cannot be
reused. Not even by duplicating.


Surprises for "small" objects
-----------------------------

Python uses lots of small objects such as Python integers in its own working,
especially in the built-in or standard modules imported to provide a working
Python environment. This can cause surprise when the variable you're meant to
track is also one of those objects. As an illustration, let us consider the
following template file:

```python
from trackrefcount import TrackRCFor
p = %NUM%
with TrackRCFor(p) as f:
    pass
f.assertEqualRC()
```

We're about to find a value for the slot `%NUM%` that breaks the assertion.
Save the file as `script-template`, and execute the following shell script:

```sh
#!/bin/sh
N=0
while [ "${N}" -lt 100 ]; do
    if ! { sed -e "s/%NUM%/${N}/g" < script-template | python 2> /dev/null ; }
    then
	printf "Offending number found: %d\n" "${N}"
	break
    fi
    N="$((N+1))"
done
unset N
```

On my computer the script's output for the "offending number" is 15. The
specific value is dependent on the Python version, the platform, and the
modules imported before the script is executed. It's possible that none may be
found to be offending at all.

Let us consider what happens with the script, with the value substituted in.

```python
from trackrefcount import TrackRCFor
p = 15
with TrackRCFor(p) as f:
    pass
f.assertEqualRC()
```

For the sake of discussion, let us first refer to "the Python integer object
meant to represent the number '15'" as *the blob*. In the above code, for
example, the Python name `p` is bound to the blob.

The following is a simplified sequence of what's happening:

1. As the context manager `f` is entered, the `sys.getrefcount()` built-in
   function is called inside the `f.__enter__()` method's body on *the blob*
   (which is referred to by the context manager itself internally).
2. This is the crucial step. The built-in function `sys.getrefcount()` is to
   create, from the actual refcount value it sees, a Python integer object --
   or more specifically, a "new reference to a Python integer object" -- to be
   returned to its caller. The refcount it sees happens to be 15, so it decides
   that the object it shall return will be the Python integer meant to
   represent the number '15', which *is* the blob (see our definition; Python
   re-uses small integers as flyweight instances and no more than one copy for
   each distinct number is created). So the act of returning this particular
   Python `int` object increases the refcount of the blob by one (the new
   reference) -- to 16 -- as a side effect, *after* the blob has been
   identified as the Python object to be returned by `sys.getrefcount()`.
3. The blob, as the object returned by `sys.getrefcount()`, is then transferred
   to a tuple attribute of our context manager instance `f`. This keeps the
   refcount to the blob at 16 all the while till the next time the function
   `sys.getrefcount()` checks on it. (This is a great simplification; what
   actually happens is a series of operations that cancel out the increase and
   decrease of the refcount). This makes `f` record the Python `int` "15" (i.e.
   the blob) as the initial value it receives from `sys.getrefcount()` at the
   time of `__enter__()`ing.
4. The empty body (`pass`) is executed, followed by the context manager's
   `__exit__()`. Inside `__exit__()`, another call to `sys.getrefcount()` is
   made. This time, just as before, the built-in function does its job: it sees
   the number 16 as the current refcount to the blob, and returns a new
   reference to the object "the Python integer object that represents the value
   '16'". This makes `f` remember `16` as the final value at the time of
   `__exit__()`ing.
5. The call to the `f.assertEqualRC()` method compares the initial and final
   values. They're not the same.

The moral of this story is that testing refcounts in Python can get tricky,
when the Python objects we use as building blocks of the test interferes with
refcounting. Small integers are the most likely to cause unexpected results.
