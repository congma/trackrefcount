class _singleton(type):
    __inst = {}
    def __call__(cls, *args, **kwargs):
        if cls in cls.__inst:
            return cls.__inst[cls]
        i = super(_singleton, cls).__call__(*args, **kwargs)
        cls.__inst[cls] = i
        return i


class __FakeNumMixin:
    """Fake number base class with common traits."""
    def __pos__(self):
        return self

    def __eq__(self, other):
        if self is other:
            return True
        if self is -other or self is ~other or self is -~other:
            return False
        return NotImplemented


class NonNegType(__FakeNumMixin, metaclass=_singleton):
    """A non-specific non-negative number."""
    def __invert__(self):
        return NegType()

    def __neg__(self):
        return NonPosType()

    def __eq__(self, other):
        p = super().__eq__(other)
        if p is not NotImplemented:
            return p
        elif other >= 0:
            return True
        else:
            return p

    def __repr__(self):
        return "NonNeg"


class NonPosType(__FakeNumMixin, metaclass=_singleton):
    """The tilde-inversion of Pos. Unlike Neg, it compares equal to zero."""
    def __invert__(self):
        return PosType()

    def __neg__(self):
        return NonNegType()

    def __eq__(self, other):
        p = super().__eq__(other)
        if p is not NotImplemented:
            return p
        elif other <= 0:
            return True
        else:
            return p

    def __repr__(self):
        return "NonPos"


class PosType(__FakeNumMixin, metaclass=_singleton):
    """Stand-in pseudo-number for unspecified positive value.
    An instance of this class compares equal to any (strictly) positive (that
    is, greater than zero) value.
    """
    def __neg__(self):
        return NegType()

    def __invert__(self):
        return NonPosType()

    def __eq__(self, other):
        p = super().__eq__(other)
        if p is not NotImplemented:
            return p
        elif other > 0:
            return True
        else:
            return p

    def __repr__(self):
        return "Pos"


class NegType(__FakeNumMixin, metaclass=_singleton):
    """Stand-in pseudo-number for unspecified negative value.
    An instance of this class compares equal to any (strictly) negative (that
    is, less than zero) value.
    """
    def __neg__(self):
        return PosType()

    def __invert__(self):
        return NonNegType()

    def __eq__(self, other):
        p = super().__eq__(other)
        if p is not NotImplemented:
            return p
        elif other < 0:
            return True
        else:
            return p

    def __repr__(self):
        return "Neg"


class AnyType(metaclass=_singleton):
    """Stand-in pseudo-number for any unspecified value."""
    def __eq__(self, other):
        return True

    def __repr__(self):
        return "Anything"


Pos = PosType()
Neg = NegType()
NonNeg = NonNegType()
NonPos = NonPosType()
Anything = AnyType()
