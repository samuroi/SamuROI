import itertools



from .artist import MaskArtist


class SetterProperty(object):
    def __init__(self, func, doc=None):
        self.func = func
        self.__doc__ = doc if doc is not None else func.__doc__

    def __set__(self, obj, value):
        return self.func(obj, value)


class PolygonArtist(MaskArtist, Polygon):
    """
    Common base class for polygon rois.
    """

    # use thin lines for inactive artists, and thick lines for active ones.
    thin = 1
    thick = 5



    @property
    def color(self):
        return self.__color

    def __init__(self, mask, **kwargs):
        MaskArtist.__init__(self, mask)


        # def add(self, axes):
        #     axes.add_artist(self.polygon)

        # def toggle_hold(self, ax):
        #     """
        #         Plot the trace on axes even if the roi is not active.
        #     """
        #     # call baseclass toggle_hold for trace handling
        #     Artist.toggle_hold(self, ax)
        #
        #     # now handle the own mask artist
        #     if len(self.holdaxes) > 0:
        #         self.polygon.set_linestyle('dashed')
        #     else:
        #         self.polygon.set_linestyle('solid')
