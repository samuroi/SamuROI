from .segmentation import Segmentation

from maskset import MaskSet
from util.event import Event

from collections import MutableSequence


class SelectionBicycle(MutableSequence):
    """
    Calls to next, prev and cur will invalidate the selection and set the respective element as selected

    All the operations on a read-only sequence.

    Concrete subclasses must provide __new__ or __init__,
    __getitem__, __setitem__, __delitem__, __len__, and insert().

    """

    def __init__(self, selection):
        self.__selection = selection
        self.__items = []
        self.__index = None

    def __getitem__(self, i):
        return self.__items[i]

    def __setitem__(self, index, value):
        self.__items[index] = value

    def __delitem__(self, index):
        del self.__items[index]
        if index == self.__index:
            self.__index = (self.__index + 1) % len(self)

    def __len__(self):
        return len(self.__items)

    def insert(self, index, value):
        result = self.__items.insert(index, value)
        if index <= self.__index:
            self.__index = self.__index + 1
        return result

    def cur(self):
        if len(self) == 0:
            item = None
        if self.__index is None:
            item = self[0]
        else:
            item = self[self.__index]
        self.__selection.clear()
        self.__selection.add(item)
        return item

    def prev(self):
        if len(self) == 0:
            item = None
        else:
            if self.__index is None or self.__index <= 0:
                self.__index = len(self) - 1
            else:
                self.__index = self.__index - 1
            item = self[self.__index]
        self.__selection.clear()
        self.__selection.add(item)
        return item

    def next(self):
        if len(self) == 0:
            item = None
        else:
            if self.__index is None or self.__index >= len(self) - 1:
                self.__index = 0
            else:
                self.__index = self.__index + 1
            item = self[self.__index]
        self.__selection.clear()
        self.__selection.add(item)
        return item


class SegmentationExtension(Segmentation):
    def __init__(self, *args, **kwargs):
        super(SegmentationExtension, self).__init__(*args, **kwargs)

        self.selection = MaskSet()

        self.__selection_cycles = dict()
        """For each type of mask, hold a bicycle list of masks to cycle through the respective group. Also hold a cycle containing all masks."""
        self.__selection_cycles["all"] = SelectionBicycle(selection=self.selection)

        # define signals
        self.active_frame_changed = Event()
        self.active_frame = 0

        # connect to base class slots
        self.masks.added.append(self._on_mask_added)
        self.masks.removed.append(self._on_mask_removed)

    @property
    def active_frame(self):
        return self.__active_frame

    @active_frame.setter
    def active_frame(self, f):
        if not 0 <= f < self.data.shape[2]:
            raise Exception("Frame needs to be in range [0,{}]".format(self.data.shape[2]))
        self.__active_frame = f
        self.active_frame_changed()

    @property
    def branch_cycle(self):
        from .masks.branch import BranchMask
        return self.__selection_cycles[BranchMask]

    @property
    def polygon_cycle(self):
        from .masks.polygon import PolygonMask
        return self.__selection_cycles[PolygonMask]

    @property
    def pixel_cycle(self):
        from .masks.pixel import PixelMask
        return self.__selection_cycles[PixelMask]

    @property
    def circle_cycle(self):
        from .masks.circle import CircleMask
        return self.__selection_cycles[CircleMask]

    @property
    def mask_cycle(self):
        return self.__selection_cycles["all"]

    def _on_mask_added(self, mask):
        # add the artist to cyclic lists which will allow easy prev/next
        self.__selection_cycles.setdefault(type(mask), SelectionBicycle(selection=self.selection)).append(mask)
        self.__selection_cycles["all"].append(mask)

    def _on_mask_removed(self, mask):
        # remove the artist from the cyclic lists
        self.__selection_cycles[type(mask)].remove(mask)
        self.__selection_cycles["all"].remove(mask)
        # if it is selected, also remove it from the selection
        self.selection.discard(mask)
