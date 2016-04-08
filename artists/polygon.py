import itertools

from matplotlib.patches import Polygon

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

    colors = {'red', 'green', 'blue', 'cyan', 'purple'}
    colorcycle = itertools.cycle(colors)

    @MaskArtist.selected.setter
    def selected(self, a):
        """ Extend the roi setter to also change linewidth of active artist."""
        if a is True:
            self.set_linewidth(self.thick)
            self.set_edgecolor(self.color)
        else:
            self.set_linewidth(self.thin)
            self.set_edgecolor('gray')

    @property
    def color(self):
        return self.__color

    def __init__(self, mask):
        MaskArtist.__init__(self, mask)
        Polygon.__init__(self, xy=mask.outline + 0.5,
                         fill=False,
                         picker=True,
                         lw=self.thin,
                         color='gray')
        self.__color = PolygonArtist.colorcycle.next()

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
