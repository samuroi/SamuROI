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

    def __init__(self, pixels, datasource, axes, **kwargs):
        """
        Arguments:
            pixels:     A 2xN array with row,column pixel coordinates.
            datasource: Handle to object holding the data.
        """
        self.datasource = datasource
        self.pixels = pixels

        artist   = axes.aximage.scatter(self.pixels[0],self.pixels[1],
                                picker = True,
                                color = PixelRoi.colorcycle.next(),
                                **kwargs)
        artist.roi = self
        super(PixelRoi,self).__init__(axes = axes, artist = artist)

    def applymask():
        data = self.datasource.data
        return data[self.pixels[0],self.pixels[1],:].mean(axis = 0)

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

