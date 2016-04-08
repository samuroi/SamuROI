from .util.event import Event

from collections import MutableSet


class MaskSet(MutableSet):
    """
    Use generic mixin functions. hence we only need to reimplement:
        __contains__, __iter__, __len__, add(), and discard().
    """

    def __init__(self, iterable=[]):
        self.__items = dict()

        self.added = Event()
        """A signal that will be triggered when an item was added to the set."""
        self.removed = Event()
        """A signal that will be triggered when an item was removed from the set."""

        for i in iterable:
            self.add(i)

    def __len__(self):
        return sum(len(value) for value in self.__items.itervalues())

    def __contains__(self, elem):
        if type(elem) not in self.__items:
            return False
        return elem in self.__items[type(elem)]

    def __iter__(self):
        for val in self.__items.itervalues():
            for i in val:
                yield i

    def __getitem__(self, type):
        return self.__items[type]

    def add(self, elem):
        _set = self.__items.setdefault(type(elem), set())
        emit = elem not in _set
        _set.add(elem)
        if emit:
            self.added(elem)

    def discard(self, elem):
        emit = elem in self.__items[type(elem)]
        self.__items[type(elem)].discard(elem)
        if emit:
            self.removed(elem)
