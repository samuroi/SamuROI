import itertools

from dumb.util import PolyMask

from matplotlib.patches import Polygon

from .roi import Roi

class PixelRoi(Roi):
    """
    A roi that is defined by a set of pixel coordinates.
    """

    colors = ['#CC0099','#CC3300','#99CC00','#00FF00','#006600','#999966']
    colorcycle = itertools.cycle(colors)

    @Roi.active.setter
    def active(self,a):
        """ Extend the roi setter to also change linewidth of active artist."""
        if a is True:
            self.artist.set_linewidth(5)
        else:
            self.artist.set_linewidth(1)
        Roi.active.fset(self,a)

    @property
    def color(self):
        return self.__color

    def __init__(self, pixels, datasource, axes, **kwargs):
        """
        Arguments:
            pixels:     A 2xN array with row,column pixel coordinates.
            datasource: Handle to object holding the data.
        """
        self.datasource = datasource
        self.pixels = pixels

        self.__color = PixelRoi.colorcycle.next()
        artist   = axes.aximage.scatter(self.pixels[0],self.pixels[1],
                                        picker = True, color = self.__color,
                                        marker = 'o',
                                        **kwargs)
        artist.roi = self
        super(PixelRoi,self).__init__(axes = axes, artist = artist)

    def applymask(self):
        data = self.datasource.data
        return data[self.pixels[1],self.pixels[0],:].mean(axis = 0)

    def toggle_hold(self,ax):
        """
            Plot the trace on axes even if the roi is not active.
        """
        # call baseclass toggle_hold for trace handling
        Roi.toggle_hold(self, ax)

        # now handle the own mask artist
        if len(self.holdaxes) > 0:
            self.artist.set_linestyle('dashed')
        else:
            self.artist.set_linestyle('solid')

