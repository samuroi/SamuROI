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
        self.preremove = Event()
        """A signal that will be triggered when an item is about to be removed from the set."""
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
                # loop over children if the mask has children:)
                # fixme actually this requires recursion...
                for child in getattr(i,"children",[]):
                    yield child

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
        if emit:
            self.preremove(elem)
        self.__items[type(elem)].discard(elem)
        if emit:
            self.removed(elem)

    def types(self):
        return self.__items.keys()


class MaskSelection(MaskSet):
    """Special handling for selection, adapts the set according to hierarchic relation between the masks"""

    def __init__(self, iterable=[]):
        super(MaskSelection, self).__init__(iterable)

    def discard(self, elem):
        """If there are elements contained which have the discareded element as parent, remove those elements as well."""
        to_remove = []
        for potential_child in self:
            if hasattr(potential_child, "parent") and potential_child.parent is elem:
                to_remove.append(potential_child)
        # remove the children first
        for child in to_remove:
            self.discard(child)
        # call base function to remove parent
        MaskSet.discard(self, elem)

    def add(self, elem):
        """Add parent to selection if element has parent"""
        if hasattr(elem, "parent"):
            self.add(elem.parent)
        MaskSet.add(self, elem)
