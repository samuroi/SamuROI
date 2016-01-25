import numpy


from ..branch import Branch
from .polyroi import PolygonRoi
from .segmentroi import SegmentRoi

from dumb.util import bicycle

class BranchRoi(Branch,PolygonRoi):
    """
        Extend the PolygonRoi with children, splitting and segment selection.
    """

    # override PolygonRoi default thickness for not so thick branches
    thick = 3

    @property
    def active_segment(self):
        """The active segment if any, None otherwise."""
        for i in self.children:
            if i.active:
                return i
        return None

    @PolygonRoi.active.setter
    def active(self,active):
        """
        Extend the polyroi active property, to also plot linescan on top axes.
        """
        # call the baseclass property setter
        PolygonRoi.active.fset(self,active)

        # plot the linescan
        if len(self.children) > 0 and active and self.imglinescan is None:
            linescan = numpy.row_stack((child.trace for child in self.children))
            tmax      = self.datasource.data.shape[-1]
            nsegments = len(self.children)
            self.imglinescan = self.axes.axraster.imshow(linescan,interpolation = 'nearest',aspect = 'auto',cmap = 'Greens', extent = (0,tmax,nsegments,0))
            self.axes.axraster.set_ylim(nsegments,0)
        elif not active and self.imglinescan is not None:
            self.imglinescan.remove()
            self.imglinescan = None


    def __init__(self, branch, datasource, axes, **kwargs):
        Branch.__init__(self, data = branch)
        PolygonRoi.__init__(self, outline = self.outline, datasource = datasource, axes = axes, **kwargs)
        #super(BranchRoi,self).__init__(data, axes = axes, **kwargs)
        self.children = []
        self.imglinescan = None
        self.__children_cycle = bicycle(self.children)

    def next_segment(self):
        if len(self.children) > 0:
            if self.active_segment is not None:
                index = self.children.index(self.active_segment)
                self.__children_cycle.i = index
            return self.__children_cycle.next()
        return None

    def previous_segment(self):
        if len(self.children) > 0:
            if self.active_segment is not None:
                index = self.children.index(self.active_segment)
                self.__children_cycle.i = index
            return self.__children_cycle.prev()
        return None


    def notify(self):
        """Override the roi notify to also update the linescan."""
        # Since the notify will also be called for branch rois if relevant data has changed, we can use the
        # branchrois notify call to update all segments of the branch immediately.
        # since the segments will have their results cached the overhead should be minimal.
        if self.imglinescan is not None:
            linescan = numpy.row_stack((child.trace for child in self.children))
            self.imglinescan.set_data(linescan)
        PolygonRoi.notify(self)

    def split(self, length):
        """Only supported if self is a root item."""
        for child in self.children:
            child.remove()

        # split branch and ist insert childrens
        # do list insertion because this will keep the children_cycle updated
        self.children[:] = [SegmentRoi(branch = child.data,
                                parent = self,
                                datasource = self.datasource,
                                axes = self.axes)
                            for child in super(BranchRoi, self).split(length = length)]

        if self.imglinescan is not None:
            linescan = numpy.row_stack((child.trace for child in self.children))
            self.imglinescan.set_data(linescan)
            tmax      = self.datasource.data.shape[-1]
            nsegments = len(self.children)
            self.imglinescan.set_extent((0,tmax,nsegments,0))
            self.axes.axraster.set_ylim(nsegments,0)
