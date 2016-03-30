from ordered_set import OrderedSet

from .util.event import Event


class RoiSet(OrderedSet):
    """
    A set of rois. Provide following additional functionality:
        - hold active item.
        - select next or previous active item
        - hold elements of only one specific type??  (TODO: think about that, is this a clever constraint?)
    """

    def __init__(self, iterable=[]):
        """

        Args:
            owner: The object that holds the roiset and will get notified about every change

        Returns:

        """
        super(RoiSet, self).__init__(iterable)

        self.added = Event()
        """A signal that will be triggered when an item was added to the set."""
        self.removed = Event()
        """A signal that will be triggered when an item was removed from the set."""
        self.__index  = None

    @property
    def active(self):
        if len(self) > 0:
            return self[self.__index]

    def copy(self):
        """Copying is forbidden since it doesnt make sense."""
        raise Exception("Not implemented")

    def add(self, elem):
        i = super(RoiSet, self).add(elem)
        if elem not in self:
            self.added(elem)
        return i

    def pop(self):
        i = super(RoiSet, self).pop()
        self.removed(i)
        return i

    def discard(self, elem):
        emit = elem in self
        i = super(RoiSet, self).discard(elem)
        if emit:
            self.removed(elem)
        return i

    def clear(self):
        items = [i for i in self]
        ret =  super(RoiSet, self).clear()
        for i in items:
            self.removed(i)
        return ret
