from .util.event import Event

from collections import MutableSet
from cached_property import cached_property


class MaskSet(MutableSet):
    """
    This class inherits from: :py:class:`collections.MutableSet`
    uses generic mixin functions and therefore only needs to reimplement the following functions:

        - `__contains__`
        - `__iter__`
        - `__len__`
        - `add()`
        - `discard()`
    """

    def __init__(self, iterable=[]):
        self.__items = dict()

        for i in iterable:
            self.add(i)

    @cached_property
    def added(self):
        """A signal that will be triggered when an item was added to the set."""
        return Event()

    @cached_property
    def preremove(self):
        """A signal that will be triggered when an item is about to be removed from the set."""
        return Event()

    @cached_property
    def removed(self):
        """A signal that will be triggered when an item was removed from the set."""
        return Event()

    def __len__(self):
        return sum(len(value) for value in iter(self.__items.values()))

    def __contains__(self, elem):
        if type(elem) not in self.__items:
            return False
        return elem in self.__items[type(elem)]

    def __iter__(self):
        for val in self.__items.values():
            for i in val:
                yield i
                # loop over children if the mask has children:)
                # fixme actually this requires recursion...
                for child in getattr(i, "children", []):
                    yield child

    def __getitem__(self, type):
        return self.__items[type]

    def add(self, elem):
        """
        Add given mask to the set if it is not already included.
        Will trigger the :py:attr:`samuroi.maskset.MaskSet.added` event in case it is added.

        :param elem: The mask to add.
        """
        _set = self.__items.setdefault(type(elem), set())
        emit = elem not in _set
        _set.add(elem)
        if emit:
            self.added(elem)

    def discard(self, elem):
        """
        Remove the given mask from the set. If the mask is not in the set do nothing.
        If a mask gets removed this will trigger :py:attr:`samuroi.maskset.MaskSet.preremove` and
        :py:attr:`samuroi.maskset.MaskSet.removed`

        :param elem: the mask to be removed.
        """
        emit = elem in self.__items[type(elem)]
        if emit:
            self.preremove(elem)
        self.__items[type(elem)].discard(elem)
        if emit:
            self.removed(elem)

    def types(self):
        """
        Get the set of different types of masks which are in the maskset.

        :return: An iterable object of types.
        """
        return list(self.__items.keys())
