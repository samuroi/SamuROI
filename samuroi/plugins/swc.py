import numpy
import numpy.linalg


def perpedndicular1(v):
    """calculate the perpendicular unit vector"""
    return numpy.array((-v[1], v[0])) / numpy.linalg.norm((-v[1], v[0]))

def normalize(v):
    return v/numpy.linalg.norm(v)

def load_swc(filename):
    return SWCFile(filename)


class Branch(numpy.recarray):
    """
    Represent a dendrite branch, or part of a dendrite branch.
    Provide functionality for splitting, drawing a polygon and iterating
    over segments.
    """

    def __new__(cls, *args,**kwargs):
        #print "new", args,kwargs
        slice = args[0]
        # if this is a branch creation via view, then we need to modify the branch
        if type(args[0]) is SWCFile:
            if not (slice.kind == slice.kind[0]).all():
                print "WARNING: Weird swc file detected: Segments of branch are not of uniform kind!"

            if not (slice.parent_id[1:] == slice.id[:-1]).all():
                raise Exception("All elements of a branch have to be connected via parent id")
            obj = slice[['x','y','z','radius']].view(Branch)
            obj.kind = slice.kind[0]
            return obj
        elif len(args) == 5:
            kind,x,y,z,r = args
            # create from 4 arrays giving x,y,z and r
            dtype  = [('x',float),('y',float),('z',float),('radius',float)]
            obj= numpy.rec.fromarrays([x,y,z,r], dtype = dtype).view(Branch)
            obj.kind = kind
            return obj
        else:
            raise Exception("Invalid number of arguments, either use kind,x,y,z,r or a slice of a swc file.")


    def __init__(self,*args):
        """Can be constructed as Branch(kind,x,y,z,r) or Branch(swc[start:end])."""
        pass

    def __array_finalize__(self, obj):
        # we dont want views on branches to be branches, again, so for simplicity
        # dont do anything here and just return plain recarray views
        if type(obj) is Branch:
            return


    def __repr__(self):
        return str(self.kind) + " " + repr(self.view(numpy.recarray))


    @property
    def corners(self):
        """
        Nx2x2 array, where N is the number of corners.
        The second dimension is for left and right corner.
        The last dimension holds x,y values.
        """

        if self.nsegments == 0:
            raise Exception("Corners can only be calculated for branches with at least 1 segment.")
        # the corners of the polygons for each element of the segment
        corners = numpy.empty(shape = (len(self),2,2),dtype = float)

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
        #TODO fix documentation
        """Split the branch into n subbranches"""
        if length is None:
            sublength = self.length/nsegments # the target length of the segments
        else:
            sublength = float(length)

        # get the data that requires interpolation
        x,y,z,r = self['x'],self['y'],self['z'],self['radius']

        # the cumulative length
        t = numpy.r_[0,numpy.cumsum(((x[:-1]-x[1:])**2 + (y[:-1]-y[1:])**2)**.5)]

        # create interpolation coefficients
        import scipy.interpolate
        splinecoeffs, u = scipy.interpolate.splprep([x,y,z,r], u = t, k = k, s = s)


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
        xn,yn,zn,rn = scipy.interpolate.splev(tnew,splinecoeffs)

        gen = lambda i0,i1: Branch(self.kind, xn[i0:i1],yn[i0:i1],zn[i0:i1],rn[i0:i1])

        return [gen(i0,i1+1) for i0,i1 in zip(indices[:-1],indices[1:])]

    def append(self, other, gap = False):
        if self.kind != other.kind:
            raise Exception("Cannot append two branches of different kind.")
        if not gap:
            # drop the first entry of the appended segment
            a,b = self,other[1:]
        else:
            a,b = self,other

        x = numpy.r_[a['x'],b['x']]
        y = numpy.r_[a['y'],b['y']]
        z = numpy.r_[a['z'],b['z']]
        r = numpy.r_[a['radius'],b['radius']]

        return Branch(self.kind,x,y,z,r)

    @property
    def nsegments(self):
        """The number of segments of this branch"""
        return len(self) - 1

    @property
    def segments(self):
        """
        Generator over quadrilateral segments of that branch.
        """
        if self.nsegments > 0:
            corners = self.corners
            for i in range(self.nsegments):
                yield numpy.row_stack((corners[i,0,:],corners[i+1,0,:],corners[i+1,1,:],corners[i,1,:]))


class SWCFile(numpy.recarray):

    swcformat = [('id',int),('kind',int),('x',float),('y',float),('z',float),
                ('radius',float),('parent_id',int)]

    def __new__(cls, *args,**kwargs):
        # if no argument is given, create zero sized recarray
        if len(args) == 0:
            args = (0,)
        elif type(args[0]) is int:
            # create empty recarray
            d = numpy.recarray(args[0], dtype = SWCFile.swcformat)
        else:
            # create from file or filename
            d = numpy.recfromtxt(args[0], dtype = SWCFile.swcformat)

        return d.view(SWCFile)

    def __init__(self,filename = None):
        self.filename = filename
        if self['id'][0] != 1:
            raise Exception("SWC id ordering needs to start with 1.")
        if not (self['id'][1:] - self['id'][:-1] == 1).all():
            raise Exception("SWC ids need to be consecutive.")


    def __array_finalize__(self, obj):
        # see InfoArray.__array_finalize__ for comments
        if obj is None: return
        self.filename = getattr(obj, 'filename', None)

    @property
    def nbranches(self):
        return (self['parent_id'] == -1).sum()

    @property
    def branches(self):
        last_index = 0
        for index in numpy.flatnonzero(self['id'] != self['parent_id'] + 1):
            if last_index == index: continue
            yield Branch(self[last_index:index])
            last_index = index
        # yield the last branch
        yield Branch(self[last_index:])
