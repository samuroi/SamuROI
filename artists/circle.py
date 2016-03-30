from .polyroi import PolygonRoi


class CircleRoi(PolygonRoi):
    """
    Fake a circle shaped roi by creating a n-faced circle like polygon.
    """

    def __init__(self, center, radius, datasource, axes):
        """
        The datasource needs to provide attributes:
            data and mask
            data needs to be WxHxT array
            and mask may be a WxH array or None
            by providint the datasource as proxy object to the PolygonRoi,
            we can easyly exchange the data in other parts of the application.
        """
        import numpy
        self.radius = radius
        self.center = center
        angle = numpy.linspace(0, 2 * numpy.pi, 100)
        x = self.radius * numpy.cos(angle) + self.center[0]
        y = self.radius * numpy.sin(angle) + self.center[1]
        outline = numpy.column_stack((x, y))
        super(CircleRoi, self).__init__(outline=outline, datasource=datasource, axes=axes)
