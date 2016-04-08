import numpy
import numpy.linalg


def perpedndicular1(v):
    """calculate the perpendicular unit vector"""
    return numpy.array((-v[1], v[0])) / numpy.linalg.norm((-v[1], v[0]))


def normalize(v):
    return v / numpy.linalg.norm(v)


class Branch(object):
    """
    Represent a dendrite branch, or part of a dendrite branch.
    Provide functionality for splitting, joining and iterating over segments.
    """

    def __init__(self, data=None, x=None, y=None, z=None, r=None):
        """Can be constructed as Branch(kind,x,y,z,r) or Branch(swc[start:end])."""
        if data is not None:
            self.data = data
        else:
            dtype = [('x', float), ('y', float), ('z', float), ('radius', float)]
            self.data = numpy.rec.fromarrays([x, y, z, r], dtype=dtype)

    def __getitem__(self, item):
        return self.data[item]

    @property
    def corners(self):
        """
        Nx2x2 array, where N is the number of corners.
        The second dimension is for left and right corner.
        The last dimension holds x,y values.
        """

        if self.nquadrilaterals == 0:
            raise Exception("Corners can only be calculated for branches with at least 1 segment.")
        # the corners of the polygons for each element of the segment
        corners = numpy.empty(shape=(len(self), 2, 2), dtype=float)

        # handle first and last element
        c0 = numpy.array((self['x'][0], self['y'][0]))
        c1 = numpy.array((self['x'][1], self['y'][1]))

        corners[0, 0] = c0 + perpedndicular1(c1 - c0) * self['radius'][0]
        corners[0, 1] = c0 - perpedndicular1(c1 - c0) * self['radius'][0]

        c0 = numpy.array((self['x'][-1], self['y'][-1]))
        c1 = numpy.array((self['x'][-2], self['y'][-2]))

        corners[-1, 0] = c0 + perpedndicular1(-c1 + c0) * self['radius'][-1]
        corners[-1, 1] = c0 - perpedndicular1(-c1 + c0) * self['radius'][-1]

        # handle the intermediate segments
        for i, (s0, s1, s2) in enumerate(zip(self[0:-2], self[1:-1], self[2:])):
            c0 = numpy.array((s0['x'], s0['y']))
            c1 = numpy.array((s1['x'], s1['y']))
            c2 = numpy.array((s2['x'], s2['y']))

            # perpendicular unit vectors
            pv01 = perpedndicular1(c1 - c0)
            pv12 = perpedndicular1(c2 - c1)

            corners[i + 1, 0] = c1 + s1['radius'] * normalize((pv01 + pv12) / 2.)
            corners[i + 1, 1] = c1 - s1['radius'] * normalize((pv01 + pv12) / 2.)
        return corners

    @property
    def outline(self):
        """
        Return the corners of the branch in such order that they encode a polygon.
        """
        return numpy.row_stack((self.corners[:, 0, :], self.corners[::-1, 1, :]))

    @property
    def length(self):
        dx = self['x'][1:] - self['x'][:-1]
        dy = self['y'][1:] - self['y'][:-1]
        return numpy.sqrt(dx ** 2 + dy ** 2).sum()

    def __len__(self):
        return len(self.data)

    def split(self, nsegments=2, length=None, k=1, s=0):
        """Split the branch into segments"""
        if length is None:
            sublength = self.length / nsegments  # the target length of the segments
        else:
            sublength = float(length)

        # get the data that requires interpolation
        x, y, z, r = self['x'], self['y'], self['z'], self['radius']

        # the cumulative length
        t = numpy.r_[0, numpy.cumsum(((x[:-1] - x[1:]) ** 2 + (y[:-1] - y[1:]) ** 2) ** .5)]

        # create interpolation coefficients
        import scipy.interpolate
        splinecoeffs, u = scipy.interpolate.splprep([x, y, z, r], u=t, k=k, s=s)

        # create new parametrization array. It is supposed to consist of the old lengths
        # plus points that cut the length into the proper segment size
        tnew = t.tolist()
        # the indices where to split the resulting tnew
        indices = [0]
        import bisect
        for n in range(1, int(self.length / sublength) + 1):
            index = bisect.bisect_left(tnew, n * sublength)
            indices.append(index)
            bisect.insort_left(tnew, n * sublength)

        # append the end index for the last segment if last segment size is larger than eps
        if tnew[-1] - tnew[-2] > 0.01:
            indices.append(len(tnew))

        # interpolate the parametrization
        xn, yn, zn, rn = scipy.interpolate.splev(tnew, splinecoeffs)

        branchgen = lambda i0, i1: Branch(x=xn[i0:i1], y=yn[i0:i1], z=zn[i0:i1], r=rn[i0:i1])
        return [branchgen(i0, i1 + 1) for i0, i1 in zip(indices[:-1], indices[1:])]

    def append(self, other, gap=False):
        if not gap:
            # drop the first entry of the appended segment
            a, b = self, other[1:]
        else:
            a, b = self, other

        x = numpy.r_[a['x'], b['x']]
        y = numpy.r_[a['y'], b['y']]
        z = numpy.r_[a['z'], b['z']]
        r = numpy.r_[a['radius'], b['radius']]

        return Branch(x=x, y=y, z=z, r=r)

    @property
    def nquadrilaterals(self):
        """The number of segments of this branch"""
        return len(self) - 1

    @property
    def quadrilaterals(self):
        """
        Generator over quadrilateral segments of that branch.
        """
        if self.nquadrilaterals > 0:
            corners = self.corners
            for i in range(self.nquadrilaterals):
                yield numpy.row_stack((corners[i, 0, :], corners[i + 1, 0, :], corners[i + 1, 1, :], corners[i, 1, :]))
