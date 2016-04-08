from ordered_set import OrderedSet

from .util.event import Event

from collections import Sized, Iterable, Container


class MaskSet(Sized, Iterable, Container):
    """
    A set of rois. Provide following additional functionality:
        - hold active item.
        - select next or previous active item
        - hold elements of only one specific type??  (TODO: think about that, is this a clever constraint?)
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
        set = self.__items.setdefault(type(elem), OrderedSet())
        emit = elem not in set
        set.add(elem)
        if emit:
            self.added(elem)

    def remove(self, elem):
        if type(elem) not in self.__items:
            raise KeyError("no elemts of given type in roiset")
        self.__items[type(elem)].remove(elem)
        self.removed(elem)
