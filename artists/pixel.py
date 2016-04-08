import itertools

from .artist import MaskArtist
from matplotlib.patches import Polygon


class PixelArtist(MaskArtist,Polygon):
    """
    A roi that is defined by a set of pixel coordinates.
    """

    colors = ['#CC0099', '#CC3300', '#99CC00', '#00FF00', '#006600', '#999966']
    colorcycle = itertools.cycle(colors)

    # @Artist.active.setter
    # def active(self, a):
    #     """ Extend the roi setter to also change linewidth of active artist."""
    #     if a is True:
    #         self.scatter.set_linewidth(5)
    #     else:
    #         self.scatter.set_linewidth(1)
    #     Artist.active.fset(self, a)

    @MaskArtist.selected.setter
    def selected(self, a):
        """ Extend the roi setter to also change linewidth of active artist."""
        if a is True:
            self.set_linewidth(2)
            self.set_edgecolor(self.color)
        else:
            self.set_linewidth(1)
            self.set_edgecolor('gray')

    @property
    def color(self):
        return self.__color

    def __init__(self, mask):
        MaskArtist.__init__(self,mask)
        Polygon.__init__(self,xy = [[1,2],[3,4]])
        # super(PixelArtist, self).__init__(mask, parent)

        self.__color = PixelArtist.colorcycle.next()
        # self.scatter = parent.aximage.scatter(mask.x, mask.y,
        #                                       picker=True, color='gray',
        #                                       marker='o'
        #                                       )
        # self.scatter.roi = self

    # def toggle_hold(self, ax):
    #     """
    #         Plot the trace on axes even if the roi is not active.
    #     """
    #     Artist.toggle_hold(self, ax)
