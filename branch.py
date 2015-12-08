import numpy
import numpy.linalg


def perpedndicular1(v):
    """calculate the perpendicular unit vector"""
    return numpy.array((-v[1], v[0])) / numpy.linalg.norm((-v[1], v[0]))

def normalize(v):
    return v/numpy.linalg.norm(v)


class Branch(object):
    """
    Represent a dendrite branch, or part of a dendrite branch.
    Provide functionality for splitting, drawing a polygon and iterating
    over segments.
    """

    def __init__(self,data):
        if len(data) < 2:
            raise ValueError("Data length is to small, need at least a quadrilateral!")
        self.__data = data

    def __getitem__(self,key):
        return self.__data[key]

    @property
    def corners(self):
        """
        Nx2x2 array, where N is the number of corners.
        The second dimension is for left and right corner.
        The last dimension holds x,y values.
        """

        if "corners" in self.__data.dtype.fields:
            return self['corners']

        # the corners of the polygons for each element of the segment
        corners = numpy.empty(shape = (len(self.__data),2,2),dtype = float)

        # handle first and last element
        c0 = numpy.array((self['x'][0],self['y'][0]))
        c1 = numpy.array((self['x'][1],self['y'][1]))

        corners[0,0] = c0 + perpedndicular1(c1-c0)*self['radius'][0]
        corners[0,1] = c0 - perpedndicular1(c1-c0)*self['radius'][0]

        c0 = numpy.array((self['x'][-1],self['y'][-1]))
        c1 = numpy.array((self['x'][-2],self['y'][-2]))

        corners[-1,0] = c0 + perpedndicular1(-c1+c0)*self['radius'][-1]
        corners[-1,1] = c0 - perpedndicular1(-c1+c0)*self['radius'][-1]

        # handle the intermediate segments
        for i,(s0,s1,s2) in enumerate(zip(self[0:-2],self[1:-1],self[2:])):
            c0 = numpy.array((s0['x'],s0['y']))
            c1 = numpy.array((s1['x'],s1['y']))
            c2 = numpy.array((s2['x'],s2['y']))

            # perpendicular unit vectors
            pv01 = perpedndicular1(c1-c0)
            pv12 = perpedndicular1(c2-c1)

            corners[i+1,0] = c1+s1['radius']*normalize((pv01+pv12)/2.)
            corners[i+1,1] = c1-s1['radius']*normalize((pv01+pv12)/2.)
        return corners

    @property
    def outline(self):
        """
        Return the corners of the branch in such order that they encode a polygon.
        """
        return numpy.row_stack((self.corners[:,0,:],self.corners[::-1,1,:]))

    @property
    def length(self):
        dx = self['x'][1:] - self['x'][:-1]
        dy = self['y'][1:] - self['y'][:-1]
        return numpy.sqrt(dx**2 + dy**2).sum()

    def split(self, nsegments = 2, length = None, k = 1, s = 0):
        """Split the branch into n subbranches"""
        if length is None:
            sublength = self.length/nsegments # the target length of the segments
        else:
            sublength = float(length)

        # get the data that requires interpolation
        x,y,z = self['x'],self['y'],self['z'] #,self['radius']
        lcx = self.corners[:,0,0]
        lcy = self.corners[:,0,1]
        rcx = self.corners[:,1,0]
        rcy = self.corners[:,1,1]

        # the cumulative length
        t = numpy.r_[0,numpy.cumsum(((x[:-1]-x[1:])**2 + (y[:-1]-y[1:])**2)**.5)]

        # create interpolation coefficients
        import scipy.interpolate
        splinecoeffs, u = scipy.interpolate.splprep([x,y,z,lcx,lcy,rcx,rcy], u = t, k = k, s = s)


        # create new parametrization array. It is supposed to consist of the old lengths
        # plus points that cut the length into the proper segment size
        tnew    = t.tolist()
        # the indices where to split the resulting tnew
        indices = [0]
        import bisect
        for n in range(1,int(self.length/sublength)+1):
            index = bisect.bisect_left(tnew,n*sublength)
            indices.append(index)
            bisect.insort_left(tnew,n*sublength)

        # append the end index for the last segment if last segment size is larger than eps
        if tnew[-1] - tnew[-2] > 0.01:
            indices.append(len(tnew))

        # interpolate the parametrization
        xn,yn,zn,lcxn,lcyn,rcxn,rcyn = scipy.interpolate.splev(tnew,splinecoeffs)

        # put the corners into the correct shape
        cornersn = numpy.array([[lcxn,lcyn],[rcxn,rcyn]]).transpose((2,0,1))

        dtype = [('x',float),('y',float),('z',float),('corners',float,(2,2))]

        gen = lambda i0,i1: Branch(numpy.rec.fromarrays([xn[i0:i1],yn[i0:i1],zn[i0:i1],cornersn[i0:i1]],
                                            dtype = dtype))

        return [gen(i0,i1+1) for i0,i1 in zip(indices[:-1],indices[1:])]

    def append(self, other, gap = False):
        if not gap:
            # drop the first entry of the appended segment
            a,b = self,other[1:]
        else:
            a,b = self,other
        x = numpy.r_[a['x'],b['x']]
        y = numpy.r_[a['y'],b['y']]
        z = numpy.r_[a['z'],b['z']]

        lcx = numpy.r_[a.corners[:,0,0],b.corners[:,0,0]]
        lcy = numpy.r_[a.corners[:,0,1],b.corners[:,0,1]]
        rcx = numpy.r_[a.corners[:,1,0],b.corners[:,1,0]]
        rcy = numpy.r_[a.corners[:,1,1],b.corners[:,1,1]]
        corners = numpy.array([[lcx,lcy],[rcx,rcy]]).transpose((2,0,1))

        dtype = [('x',float),('y',float),('z',float),('corners',float,(2,2))]
        return Branch(numpy.rec.fromarrays([x,y,z,corners], dtype = dtype))

    @property
    def nsegments(self):
        """The number of segments of this branch"""
        return len(self.__data) - 1

    @property
    def segments(self):
        """
        Generator over quadrilateral segments of that branch.
        """
        corners = self.corners
        for i in range(self.nsegments):
            yield numpy.row_stack((corners[i,0,:],corners[i+1,0,:],corners[i+1,1,:],corners[i,1,:]))

    """
    def polymasks(self,shape, outline = True):
        from PIL import Image, ImageDraw
        img = Image.new('I', (shape[1],shape[0]),0)
        for i, roi in enumerate(self.polygons):
            l = [(r[0],r[1]) for r in roi]
            ImageDraw.Draw(img).polygon(xy = l, outline = i+1 if outline else 0, fill=i+1)
            yield numpy.where(numpy.array(img) == i+1)
    """
