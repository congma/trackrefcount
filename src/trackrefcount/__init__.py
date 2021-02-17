"""Module trackrefcount.

The module provides a context manager class, TrackRCFor, that eases the
application of boilerplate code to track the referene count of Python objects.
"""
from .cm import TrackRCFor
from ._pseudo_nums import Pos, Neg, NonPos, NonNeg, Anything


__all__ = ["TrackRCFor", "Pos", "Neg", "NonPos", "NonNeg", "Anything"]
