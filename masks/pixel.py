from .mask import Mask


class PixelMask(Mask):
    def __init__(self, xy, x=None, y=None):
        # use private variables and properties because masks should be either immutable or use changed signal.
        self.__x, self.__y = xy

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    def __call__(self, data, mask):
        data = self.datasource.data
        return data[self.pixels[1], self.pixels[0], :].mean(axis=0)
        raise NotImplementedError("")
