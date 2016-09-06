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

    def __init__(self, data=None, x=None, y=None, z=None, r=None, name=None):
        """Can be constructed as Branch(kind,x,y,z,r) or Branch(swc[start:end])."""
        Mask.__init__(self, name=name)
        Branch.__init__(self, data, x, y, z, r)

        self.segments = []
        """Child masks aka segments of the branch."""

        from .polygon import PolygonMask
        self.__polygon = PolygonMask(outline=self.outline)

        self.changed = Event()

    @property
    def children(self):
        return self.segments

    def __call__(self, data, mask):
        return self.__polygon(data, mask)

    def to_hdf5(self, f):
        if 'branches' not in f:
            f.create_group('branches')
        f.create_group('branches/' + self.name)
        f.create_dataset('branches/' + self.name + '/data', data=self.data)
        f.create_dataset('branches/' + self.name + '/outline', data=self.outline)

        if len(self.children) > 0:
            f.create_group('branches/' + self.name + '/segments')
            for s in self.children:
                f.create_group('branches/{}/segments/{}'.format(self.name, s.name))
                f.create_dataset('branches/{}/segments/{}/data'.format(self.name, s.name), data=s.data)
                f.create_dataset('branches/{}/segments/{}/outline'.format(self.name, s.name), data=s.outline)

    @staticmethod
    def from_hdf5(f):
        from .polygon import PolygonMask
        if 'branches' in f:
            for name in f['branches'].keys():
                data = f['branches/' + name + '/data'].value
                branch = BranchMask(name=name, data=data)
                if 'segments' in f['branches/' + name]:
                    for childname in f['branches/' + name + '/segments'].keys():
                        child = PolygonMask(name=childname,
                                            outline=f['branches/' + name + '/segments/' + childname + '/outline'].value)
                        branch.children.append(child)
                yield branch

    def split(self, nsegments=2, length=None, k=1, s=0):
        branches = Branch.split(self, nsegments=nsegments, length=length, k=k, s=s)
        self.segments = [SegmentMask(data=b.data, parent=self) for b in branches]
        self.changed(self)

    def linescan(self, data, mask):
        """
        Calculate the trace for all children and return a 2D array aka linescan for that branch roi.
        """
        return numpy.row_stack((child(data, mask) for child in self.segments))

    def append(self, other, gap=False):
        raise NotImplementedError("not supported for branchmask")
