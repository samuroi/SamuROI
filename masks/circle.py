from .mask import Mask


class CircleMask(Mask):
    def __init__(self, center, radius):
        super(CircleMask,self).__init__()
        # use private variables and properties because masks should be either immutable or use changed signal.
        self.__center = center
        self.__radius = radius

        import numpy
        angle = numpy.linspace(0, 2 * numpy.pi, 100)
        x = self.radius * numpy.cos(angle) + self.center[0]
        y = self.radius * numpy.sin(angle) + self.center[1]
        corners = numpy.column_stack((x, y))
        from .polygon import PolygonMask
        self.__polygon = PolygonMask(corners=corners)

    @property
    def center(self):
        return self.__center

    @property
    def radius(self):
        return self.__radius

    def __call__(self, data, mask):
        return self.__polygon(data, mask)
