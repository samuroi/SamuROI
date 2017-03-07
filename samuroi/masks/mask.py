from abc import abstractmethod


class Mask(object):
    """If a mask is mutable, it needs to provide a changed signal, which is supposed to be triggered upon modification."""

    # count created objects, useful for creating suffixes
    __count = {}

    def __init__(self, name=None):
        if name is None:
            self.name = type(self).__name__ + self.__suffix()
        else:
            self.name = name

    @abstractmethod
    def __call__(self, data, mask):
        """
        Apply self on data and calculate the time trace. Before the application of self, the data is masked
        with the mask provided in the parameters.
        I.e. the final resulting mask is an `and` composition of self and mask.

        :param data: the video data .
        :param mask: a 2D mask array with same shape as video resolution.
        :return: 1D numpy array holding the time trace of this mask.
        """
        raise NotImplementedError()

    @abstractmethod
    def to_hdf5(self, f):
        """
        Save the mask to to an opened hd5 file.
        :param f: the hd5 file handle.
        """
        raise NotImplementedError()

    def __suffix(self):
        if type(self) not in Mask.__count:
            Mask.__count[type(self)] = -1
        Mask.__count[type(self)] += 1
        return '#' + str(Mask.__count[type(self)])
