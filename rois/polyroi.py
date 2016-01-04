import itertools

from dumb.util import PolyMask

from matplotlib.patches import Polygon

from .roi import Roi

class PolygonRoi(Roi):
    """
    Common base class for polygon rois.
    """


    colors = ['#CC0099','#CC3300','#99CC00','#00FF00','#006600','#999966']
    colorcycle = itertools.cycle(colors)

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
        self.polymask = outline.view(PolyMask)
        artist   = Polygon(outline, fill = False,
                                picker = True,
                                lw  = self.thin,
                                color = PolygonRoi.colorcycle.next(),
                                **kwargs)
        artist.roi = self
        super(PolygonRoi,self).__init__(axes = axes, artist = artist)

        if axes is not None:
            axes.aximage.add_artist(self.artist)

    def applymask():
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

