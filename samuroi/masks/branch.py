import numpy
import numpy.linalg

from .mask import Mask
from ..util.event import Event
from ..util.branch import Branch

from .segment import SegmentMask


class BranchMask(Mask):
    """
    Represent a dendrite branch, or part of a dendrite branch.
    Provide functionality for splitting, joining and iterating over segments.
    """

    def __init__(self, data=None, name=None):
        """Can be constructed as Branch(kind,x,y,z,r) or Branch(swc[start:end])."""
        super(BranchMask, self).__init__(name=name)
        self.branch = Branch(data=data)

        self.segments = []
        """Child masks aka segments of the branch."""

        from .polygon import PolygonMask
        self.__polygon = PolygonMask(outline=self.outline)

        self.changed = Event()
        """The event which will be triggered when the branch mask was changed."""

    @property
    def outline(self):
        """
        :return: return the outline of the wrapped :py:class:`samuroi.util.branch.Branch` object.
        """
        return self.branch.outline

    @property
    def data(self):
        """
        :return: return the data of the wrapped :py:class:`samuroi.util.branch.Branch` object.
        """
        return self.branch.data

    @property
    def children(self):
        """
        Get the list of child segments of this branch.

        .. warning::
            Do not modify this list manually. Instead use :py:func:`samuroi.masks.branch.BranchMask.split`.

        :return: the list of children.
        """
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
        if 'branches' in f:
            for name in f['branches'].keys():
                data = f['branches/' + name + '/data'].value
                branch = BranchMask(name=name, data=data)
                if 'segments' in f['branches/' + name]:
                    for childname in f['branches/' + name + '/segments'].keys():
                        child = SegmentMask(parent=branch,
                                            data=f['branches/' + name + '/segments/' + childname + '/data'].value)
                        child.name = childname
                        branch.children.append(child)
                yield branch

    def move(self, offset):
        """Move the branch and all its children."""

        new_x = self.data['x'] + offset[0]
        new_y = self.data['y'] + offset[1]

        dtype = [('x', float), ('y', float), ('z', float), ('radius', float)]
        self.branch.data = numpy.rec.fromarrays([new_x, new_y, self.data['z'], self.data['radius']], dtype=dtype)

        from .polygon import PolygonMask
        self.__polygon = PolygonMask(outline=self.outline)

        for child in self.segments:
            child.move(offset)

        self.changed(self)

    def split(self, nsegments=2, length=None, k=1, s=0):
        """
        Split this branch and create a set of child segments.

        .. note::
            One can either provide a `nsegments` or `length`.

        Splitting of a branch will modify the :py:attr:`samuroi.masks.branch.BranchMask.children` attribute
        and hence trigger a :py:attr:`samuroi.masks.branch.BranchMask.changed` event.

        :param nsegments: the number of segments.
        :param length: the length of each segment (the last segment will have the remainder of modulo division).
        :param k: smoothness parameter for spline interpolation
        :param s: smoothness parameter for spline interpolation
        """
        branches = self.branch.split(nsegments=nsegments, length=length, k=k, s=s)
        self.segments = [SegmentMask(data=b.data, parent=self) for b in branches]
        self.changed(self)

    def linescan(self, data, mask):
        """
        Calculate the trace for all children and return a 2D array of traces.
        :param data: the data to apply on.
        :param mask: some additional overlay mask
        :return: 2D numpy array holding traces for all children
        """
        return numpy.row_stack((child(data, mask) for child in self.segments))

    def append(self, other, gap=False):
        raise NotImplementedError("not supported for branchmask")
