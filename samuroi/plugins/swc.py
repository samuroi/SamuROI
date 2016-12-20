import numpy

from samuroi.util.branch import Branch

def load_swc(filename):
    return SWCFile(filename)


class SWCFile(numpy.recarray):
    """
    Subclass of numpy.recarray for swc files.
    """

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
        """
        Create a numpy recarray for given swc file.
        :param filename (str): the path/filename to load.
        """
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
        """
        :return: The number of branches in the file.
        """
        return (self['parent_id'] == -1).sum()

    @property
    def branches(self):
        """
        :return: A generator object that allows to iterate over all branches.
        """
        last_index = 0
        for index in numpy.flatnonzero(self['id'] != self['parent_id'] + 1):
            if last_index == index: continue
            yield Branch(self[last_index:index][['x','y','z','radius']])
            last_index = index
        # yield the last branch
        yield Branch(self[last_index:])
