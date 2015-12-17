import itertools

from .branch import Branch

from dumb.util import PolyMask

from matplotlib.patches import Polygon

class PolygonRoi(Branch):
    """
    Extend the pure branch to also handle artist, trace and selection attributes.
    """

    colors = ['#CC0099','#CC3300','#99CC00','#00FF00','#006600','#999966']
    colorcycle = itertools.cycle(colors)

    thick = 5
    thin  = 1

    def __init__(self, data, axes, parent = None, **kwargs):
        super(PolygonRoi,self).__init__(data)

        self.axes     = axes
        self.polymask = self.outline.view(PolyMask)
        self.artist   = Polygon(self.outline, fill = False,
                                picker = False,
                                lw  = PolygonRoi.thin,
                                color = PolygonRoi.colorcycle.next(),
                                **kwargs)
        self.__active = False
        if axes is not None:
            axes.add_artist(self.artist)
    @property
    def active(self):
        return self.__active

    @active.setter
    def active(self, active):
        if active:
            self.artist.set_linewidth(PolygonRoi.thick)
        else:
            self.artist.set_linewidth(PolygonRoi.thin)
        self.__active = active

    #active = property(_get_active,_set_active)
