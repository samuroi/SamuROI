import itertools

from dumb.util import PolyMask

from matplotlib.patches import Polygon

from .roi import Roi

class PolygonRoi(Roi):
    """
    Common base class for polygon rois.
    """

    # use thin lines for inactive artists, and thick lines for active ones.
    thin  = 1
    thick = 5

    colors = {'red', 'green', 'blue', 'cyan', 'purple'}
    colorcycle = itertools.cycle(colors)

    @Roi.active.setter
    def active(self,a):
        """ Extend the roi setter to also change linewidth of active artist."""
        if a is True:
            self.artist.set_linewidth(self.thick)
            self.artist.set_edgecolor(self.active_color)
        else:
            self.artist.set_linewidth(self.thin)
            self.artist.set_edgecolor('gray')
        Roi.active.fset(self,a)

    @property
    def color(self):
        return self.artist.get_edgecolor()

    def __init__(self, outline, datasource, axes, **kwargs):
        """
        The datasource needs to provide attributes:
            data and mask
            data needs to be WxHxT array
            and mask may be a WxH array or None
            by providint the datasource as proxy object to the PolygonRoi,
            we can easyly exchange the data in other parts of the application.
        """
        self.datasource = datasource
        self.outline = outline
        copy = outline.copy()
        copy = copy + 0.5
        self.polymask = copy.view(PolyMask)
        artist   = Polygon(outline, fill = False,
                                picker = True,
                                lw  = self.thin,
                                color = 'gray',# PolygonRoi.colorcycle.next(),
                                **kwargs)
        artist.roi = self
        self.active_color = PolygonRoi.colorcycle.next()
        super(PolygonRoi,self).__init__(axes = axes, artist = artist)

        if axes is not None:
            axes.aximage.add_artist(self.artist)

    def applymask(self):
        data = self.datasource.data
        mask = self.datasource.mask
        return self.polymask(data = data, mask = mask)


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

