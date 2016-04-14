import numpy

from .polygon import PolygonArtist
from .segment import SegmentArtist

from dumb.util import bicyclelist


class BranchArtist(PolygonArtist):
    """
        Extend the PolygonRoi with children, splitting and segment selection.
    """

    # override PolygonRoi default thickness for not so thick branches
    thick = 3

    def __init__(self, mask):
        super(BranchArtist, self).__init__(mask)
        self.children = []
        self.mask.changed.append(self.on_mask_change)

        # update sub artists
        self.on_mask_change(self.mask)

    def on_mask_change(self, mask):
        """Will be called when the branch masks number of children change."""

        # remove all old children
        for child in self.children:
            child.remove()
        self.children = []

        for segment in self.mask.segments:
            child = SegmentArtist(segment, self)
            self.axes.add_artist(child)
            self.children.append(child)

    def remove(self):
        for child in self.children:
            child.remove()
        PolygonArtist.remove(self)
        #
        # @property
        # def active_segment(self):
        #     """The active segment if any, None otherwise."""
        #     for i in self.children:
        #         if i.active:
        #             return i
        #     return None
        #
        # @property
        # def linescan(self):
        #     """
        #     Calculate the trace for all children and return a 2D array aka linescan for that branch roi.
        #     """
        #     return numpy.row_stack((child.trace for child in self.children))
        #
        # @PolygonArtist.active.setter
        # def active(self, active):
        #     """
        #     Extend the polyroi active property, to also plot linescan on top axes.
        #     """
        #     # call the baseclass property setter
        #     PolygonArtist.active.fset(self, active)
        #
        #
        #     elif not active and self.imglinescan is not None:
        #         self.imglinescan.remove()
        #         self.imglinescan = None
        #
        # def next_segment(self):
        #     if len(self.children) > 0:
        #         return self.children.next()
        #     return None
        #
        # def previous_segment(self):
        #     if len(self.children) > 0:
        #         return self.children.prev()
        #     return None
        #
        # def notify(self):
        #     """Override the roi notify to also update the linescan."""
        #     # Since the notify will also be called for branch rois if relevant data has changed, we can use the
        #     # branchrois notify call to update all segments of the branch immediately.
        #     # since the segments will have their results cached the overhead should be minimal.
        #     PolygonArtist.notify(self)
        #     if self.imglinescan is not None:
        #         ls = self.linescan
        #         self.imglinescan.set_data(ls)
        #         self.imglinescan.set_clim(ls.min(), ls.max())
        #
