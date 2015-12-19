import itertools

from dumb.util import PolyMask

from matplotlib.patches import Polygon

class PolygonRoi(object):
    """
    Extend the pure branch to also handle artist, trace and selection attributes.
    """

    colors = ['#CC0099','#CC3300','#99CC00','#00FF00','#006600','#999966']
    colorcycle = itertools.cycle(colors)

    thick = 5
    thin  = 1

    class TraceCache(dict):
        """
        notify all rois with cached traces to update their plots on cach clearing.
        """
        def clear(self):
            rois = self.keys()
            dict.clear(self)
            for roi in rois:
                roi.notify()

    tracecache = TraceCache()

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
        self.axes     = axes
        self.polymask = outline.view(PolyMask)
        self.artist   = Polygon(outline, fill = False,
                                picker = False,
                                lw  = PolygonRoi.thin,
                                color = PolygonRoi.colorcycle.next(),
                                **kwargs)
        self.__active = False

        self.holdaxes  = []
        """the list of axes where this roi actually holds a trace"""
        self.holdlines = {}
        """a mapping from the axes where the roi holds a trace, to the line artist"""

        if axes is not None:
            axes.aximage.add_artist(self.artist)

    @property
    def color(self):
        return self.artist.get_edgecolor()

    @property
    def trace(self):
        if self not in PolygonRoi.tracecache:
            data = self.datasource.data
            mask = self.datasource.mask
            PolygonRoi.tracecache[self] = self.polymask(data = data, mask = mask)
        return PolygonRoi.tracecache[self]

    def remove(self):
        """remove all artists and traces"""
        self.artist.remove()
        if hasattr(self,"traceline"):
            self.traceline.remove()
        for line in self.holdlines.values():
            line.remove()
        if self in PolygonRoi.tracecache:
            del PolygonRoi.tracecache[self]


    def notify(self):
        """ this method is supposed to be called when the trace data has changed."""
        # update the trace of active line
        if hasattr(self,"traceline"):
            trace = self.trace
            x,_ = self.traceline.get_data()
            self.traceline.set_data(x,trace)

        # update the holded traces
        for line in self.holdlines.values():
            x,_ = line.get_data()
            line.set_data(x,self.trace)

    def toggle_hold(self,ax):
        """
            Plot the trace on axes even if the roi is not active.
        """
        if ax in self.holdaxes:
            self.holdlines[ax].remove()
            del self.holdlines[ax]
            self.holdaxes.remove(ax)
        else:
            self.holdaxes.append(ax)
            line, = ax.plot(self.trace, color = self.color)
            self.holdlines[ax] = line
        if len(self.holdaxes) > 0:
            self.artist.set_fill(True)
            self.artist.set_alpha(0.35)
        else:
            self.artist.set_fill(False)
            self.artist.set_alpha(1)

    @trace.deleter
    def trace(self):
        if self in PolygonRoi.tracecache:
            del PolygonRoi.tracecache[self]

    @property
    def active(self):
        return self.__active

    @active.setter
    def active(self, active):
        if active:
            self.artist.set_linewidth(PolygonRoi.thick)
            self.traceline, = self.axes.axtraceactive.plot(self.trace, color = self.color)
        else:
            if hasattr(self,"traceline") and self.traceline in self.axes.axtraceactive.lines:
                self.traceline.remove()
                del self.traceline
            self.artist.set_linewidth(PolygonRoi.thin)
        self.__active = active

    #active = property(_get_active,_set_active)
