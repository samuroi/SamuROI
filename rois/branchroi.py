
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

    @PolygonRoi.active.setter
    def active(self,active):
        """
        Extend the polyroi active property, to also deactivate contained segments.
        """
        if active == False:
            self.active_segment = None
        # call the baseclass property setter
        PolygonRoi.active.fset(self,active)

    def __init__(self, branch, datasource, axes, **kwargs):
        Branch.__init__(self, data = branch)
        PolygonRoi.__init__(self, outline = self.outline, datasource = datasource, axes = axes, **kwargs)
        #super(BranchRoi,self).__init__(data, axes = axes, **kwargs)
        self.children = []
        self.__children_cycle = bicycle(self.children)

    def next_segment(self):
        if len(self.children) > 0:
            return self.__children_cycle.next()
        return None

    def previous_segment(self):
        if len(self.children) > 0:
            return self.__children_cycle.prev()
        return None

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
