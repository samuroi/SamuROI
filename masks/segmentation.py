import numpy

from .mask import Mask


class Segmentation(Mask):
    """
    Represent a full segmentation of the 2D array. The segmentation should be immutable.
    Maybe a special handling for index 0 would be nice?!?
    """

    class Child(Mask):
        """A proxy object that implements the mask interface but is just a facade around one index of the segmentation."""

        def __init__(self, parent, index):
            Mask.__init__(self, name=parent.name + ": " + str(index))
            self.__index = index
            self.__parent = parent
            self.__y, self.__x = numpy.where(parent.data == index)

        def __call__(self, data, mask):
            # get a view on the data for own pixels. shape N x T where N is number of pixels
            data_p = data[self.__y, self.__x, :]
            # get a view on the mask for own pixels. shape N x 1 for broadcasting
            mask_p = mask[self.__y, self.__x].reshape(-1, 1)

            return (data_p * mask_p).mean(axis=0)

        @property
        def x(self):
            return self.__x

        @property
        def y(self):
            return self.__y

        @property
        def parent(self):
            return self.__parent

    def __init__(self, data, name=None):
        """Construct the segmetnation with given data array. The data array should have the same
        shape as the 3D dataset which will be used lateron. Otherwise mask.apply will raise an exception."""
        Mask.__init__(self, name=name)

        self.__data = data

        indices = numpy.unique(data)

        self.__children = [Segmentation.Child(self, i) for i in indices if not i == 0]

    @property
    def children(self):
        return self.__children

    @property
    def data(self):
        return self.__data

    def __call__(self, data, mask):
        return numpy.zeros(dtype=float, shape=[data.shape[-1]])

    def to_hdf5(self, f):
        if 'segmentations' not in f:
            f.create_group('segmentations')
        f.create_group('segmentations/' + self.name)
        f.create_dataset('segmentations/' + self.name + '/data', data=self.data)

    @staticmethod
    def from_hdf5(f):
        if 'segmentations' in f:
            for name in f['segmentations'].keys():
                data = f['segmentations/' + name + '/data'].value
                seg = Segmentation(name=name, data=data)
                yield seg
