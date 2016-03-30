import numpy


#from dumb.util.swc import Branch
from .polyroi import PolygonRoi
from .segmentroi import SegmentRoi

from dumb.util import bicycle

class BranchRoi(PolygonRoi):
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

    @property
    def linescan(self):
        """
        Calculate the trace for all children and return a 2D array aka linescan for that branch roi.
        """
        return numpy.row_stack((child.trace for child in self.children))

    @PolygonRoi.active.setter
    def active(self,active):
        """
        Extend the polyroi active property, to also plot linescan on top axes.
        """
        # call the baseclass property setter
        PolygonRoi.active.fset(self,active)

        # plot the linescan
        if len(self.children) > 0 and active and self.imglinescan is None:
            tmax      = self.datasource.data.shape[-1]
            nsegments = len(self.children)
            self.imglinescan = self.axes.axraster.imshow(self.linescan,interpolation = 'nearest',aspect = 'auto',cmap = 'viridis', extent = (0,tmax,nsegments,0))
            self.axes.axraster.set_ylim(nsegments,0)
        elif not active and self.imglinescan is not None:
            self.imglinescan.remove()
            self.imglinescan = None


    def __init__(self, branch, datasource, axes, **kwargs):
        #Branch.__init__(self, data = branch)
        PolygonRoi.__init__(self, outline = branch.outline, datasource = datasource, axes = axes, **kwargs)
        self.branch = branch
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
        PolygonRoi.notify(self)
        if self.imglinescan is not None:
            ls = self.linescan
            self.imglinescan.set_data(ls)
            self.imglinescan.set_clim(ls.min(),ls.max())

    def remove(self):
        for child in self.children:
            child.remove()
        PolygonRoi.remove(self)

    def split(self, length):
        """Only supported if self is a root item."""
        for child in self.children:
            child.remove()

        # split branch and ist insert childrens
        # do list insertion because this will keep the children_cycle updated
        self.children[:] = [SegmentRoi(branch = child,
                                parent = self,
                                datasource = self.datasource,
                                axes = self.axes)
                            for child in self.branch.split(length = length)]

        if self.imglinescan is not None:
            self.imglinescan.set_data(self.linescan)
            tmax      = self.datasource.data.shape[-1]
            nsegments = len(self.children)
            self.imglinescan.set_extent((0,tmax,nsegments,0))
            self.axes.axraster.set_ylim(nsegments,0)
