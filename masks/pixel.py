from .mask import Mask


class PixelMask(Mask):
    def __init__(self, xy=None, x=None, y=None):
        super(PixelMask, self).__init__()
        # use private variables and properties because masks should be either immutable or use changed signal.
        if xy is None:
            self.__x = x
            self.__y = y
        else:
            self.__x, self.__y = xy

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    def __call__(self, data, mask):
        # get a view on the data for own pixels. shape N x T where N is number of pixels
        data_p = data[self.__y, self.__x, :]
        # get a view on the mask for own pixels. shape N x 1 for broadcasting
        mask_p = mask[self.__y, self.__x].reshape(-1, 1)

        return (data_p * mask_p).sum(axis=0)
