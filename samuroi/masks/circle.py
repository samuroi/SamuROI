from .mask import Mask
from ..util.event import Event

class CircleMask(Mask):
    def __init__(self, center, radius, name=None):
        super(CircleMask, self).__init__(name=name)

        import numpy
        # use private variables and properties because masks should be either immutable or use changed signal.
        self.__center = numpy.array([center[0], center[1]])
        self.__radius = radius

        angle = numpy.linspace(0, 2 * numpy.pi, 100)
        x = self.radius * numpy.cos(angle) + self.center[0]
        y = self.radius * numpy.sin(angle) + self.center[1]
        corners = numpy.column_stack((x, y))
        from .polygon import PolygonMask
        self.__polygon = PolygonMask(outline=corners)

        self.changed = Event()

    @property
    def center(self):
        return self.__center

    @property
    def radius(self):
        return self.__radius

    def move(self, offset):
        """
        Move the circle mask in the direction defined by offset. Will trigger the changed event.
        :param offset: list with two elements denoting x (positive right, negative left) and y (positive up, negative down).
        """
        self.__center[0]+=offset[0]
        self.__center[1]+=offset[1]
        import numpy
        angle = numpy.linspace(0, 2 * numpy.pi, 100)
        x = self.radius * numpy.cos(angle) + self.center[0]
        y = self.radius * numpy.sin(angle) + self.center[1]
        corners = numpy.column_stack((x, y))
        from .polygon import PolygonMask
        self.__polygon = PolygonMask(outline=corners)

        self.changed(self)

    def to_hdf5(self, f):
        if 'circles' not in f:
            f.create_group('circles')
        data = [self.center[0], self.center[1], self.radius]
        f.create_dataset('circles/' + self.name, data=data)

    @staticmethod
    def from_hdf5(f):
        if 'circles' in f:
            for name, dataset in f['circles'].items():
                center = dataset.value[0:2]
                radius = dataset.value[2]
                yield CircleMask(name=name, center=center, radius=radius)

    def __call__(self, data, mask):
        return self.__polygon(data, mask)
