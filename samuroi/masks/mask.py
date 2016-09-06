from abc import abstractmethod


class Mask(object):
    """If a mask is mutable, it needs to provide a changed signal, which is supposed to be triggered upon modification."""

    # count created objects, useful for creating prefixes
    __count = {}

    def __init__(self, name=None):
        if name is None:
            self.name = type(self).__name__ + self.__prefix()
        else:
            self.name = name

    @abstractmethod
    def __call__(self, data, mask):
        """Apply the mask on data"""
        raise NotImplementedError()

    @abstractmethod
    def to_hdf5(self, f):
        """
        Save the mask to given hdf5 file handle.
        """
        raise NotImplementedError()

    def __prefix(self):
        if type(self) not in Mask.__count:
            Mask.__count[type(self)] = -1
        Mask.__count[type(self)] += 1
        return '#' + str(Mask.__count[type(self)])
