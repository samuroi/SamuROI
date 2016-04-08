import numpy
import numpy.linalg

from .mask import Mask
from ..util.event import Event
from ..util.branch import Branch

from .segment import SegmentMask


class BranchMask(Branch, Mask):
    """
    Represent a dendrite branch, or part of a dendrite branch.
    Provide functionality for splitting, joining and iterating over segments.
    """

    def __init__(self, data=None, x=None, y=None, z=None, r=None):
        """Can be constructed as Branch(kind,x,y,z,r) or Branch(swc[start:end])."""
        super(BranchMask, self).__init__(data, x, y, z, r)

        self.segments = []
        """Child masks aka segments of the branch."""

        from .polygon import PolygonMask
        self.__polygon = PolygonMask(corners=self.outline)

        self.changed = Event()

    def __call__(self, data, mask):
        return self.__polygon(data, mask)

    def split(self, nsegments=2, length=None, k=1, s=0):
        branches = Branch.split(self, nsegments=nsegments, length=length, k=k, s=s)
        self.segments = [SegmentMask(data=b.data, parent=self) for b in branches]
        self.changed()

    def linescan(self, data, mask):
        """
        Calculate the trace for all children and return a 2D array aka linescan for that branch roi.
        """
        return numpy.row_stack((child.apply(data, mask) for child in self.segments))

    def append(self, other, gap=False):
        raise NotImplementedError("not supported for branchmask")
