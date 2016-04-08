import itertools

from matplotlib.patches import Polygon

from .artist import Artist


class PolygonArtist(Artist):
    """
    Common base class for polygon rois.
    """

    # use thin lines for inactive artists, and thick lines for active ones.
    thin = 1
    thick = 5

    colors = {'red', 'green', 'blue', 'cyan', 'purple'}
    colorcycle = itertools.cycle(colors)

    @Artist.active.setter
    def active(self, a):
        """ Extend the roi setter to also change linewidth of active artist."""
        if a is True:
            self.polygon.set_linewidth(self.thick)
            self.polygon.set_edgecolor(self.color)
        else:
            self.polygon.set_linewidth(self.thin)
            self.polygon.set_edgecolor('gray')
        Artist.active.fset(self, a)

    @property
    def color(self):
        return self.__color

    def __init__(self, mask, parent):
        super(PolygonArtist, self).__init__(mask, parent)

        self.polygon = Polygon(mask.outline + 0.5, fill=False,
                               picker=True,
                               lw=self.thin,
                               color='gray')
        self.polygon.roi = self

        self.__color = PolygonArtist.colorcycle.next()

        parent.aximage.add_artist(self.polygon)

    def toggle_hold(self, ax):
        """
            Plot the trace on axes even if the roi is not active.
        """
        # call baseclass toggle_hold for trace handling
        Artist.toggle_hold(self, ax)

        # now handle the own mask artist
        if len(self.holdaxes) > 0:
            self.polygon.set_linestyle('dashed')
        else:
            self.polygon.set_linestyle('solid')
