import itertools

from dumb.util import PolyMask

from matplotlib.patches import Polygon

class Roi(object):
    """
    Base class for rois that allow calculating traces and have an attached matplotlib artists.
    This class handles trace updates, trace plot states, trace holding and the roi artist managment.
    """

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

    def __init__(self, axes, artist):
        self.__active = False

        self.artist = artist
        """The artist representing the mask."""

        self.axes = axes
        """an object that has a axtraceactive attribute defininf the axes where to plot the active traces"""
        self.holdaxes  = []
        """the list of axes where this roi actually holds a trace"""
        self.holdlines = {}
        """a mapping from the axes where the roi holds a trace, to the line artist"""

    def applymask(self):
        raise NotImplementedError("applymask needs to be implemented in a derived class.")

    @property
    def color(self):
        return self.artist.get_edgecolor()

    @property
    def trace(self):
        if self not in Roi.tracecache:
            Roi.tracecache[self] = self.applymask()
        return Roi.tracecache[self]

    def relim(self,axes):
        """recalculate and update the axes limit after adding/removing a line or updating via notify."""
        axes.relim()
        axes.autoscale(axis = 'y',tight = True)
        mi,ma = axes.get_ylim()
        axes.set_ylim(mi-(ma-mi)*0.1, ma+(ma-mi)*0.1)

    def remove(self):
        """remove all artists and traces"""
        self.artist.remove()
        if hasattr(self,"traceline"):
            self.traceline.remove()
        for axes,line in self.holdlines.iteritems():
            line.remove()
            # recalculate the ylim for the remaining lines
            self.relim(axes)
        if self in Roi.tracecache:
            del Roi.tracecache[self]


    def notify(self):
        """ this method is supposed to be called when the trace data has changed."""
        # update the trace of active line
        if hasattr(self,"traceline"):
            trace = self.trace
            x,_ = self.traceline.get_data()
            self.traceline.set_data(x,trace)

        # update the holded traces
        for axes,line in self.holdlines.iteritems():
            x,_ = line.get_data()
            line.set_data(x,self.trace)
            self.relim(axes)

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
            line, = ax.plot(self.trace, color = self.color, picker = 5)
            line.roi = self
            self.holdlines[ax] = line
        # because we have added/removed a line from the holdaxes, we need to relimit the axes
        self.relim(ax)

    @trace.deleter
    def trace(self):
        if self in Roi.tracecache:
            del Roi.tracecache[self]

    @property
    def active(self):
        return self.__active

    @active.setter
    def active(self, active):
        if active:
            self.artist.set_linewidth(self.thick)
            self.traceline, = self.axes.axtraceactive.plot(self.trace, color = self.color)
        else:
            if hasattr(self,"traceline") and self.traceline in self.axes.axtraceactive.lines:
                self.traceline.remove()
                del self.traceline
            self.artist.set_linewidth(self.thin)
        self.relim(self.axes.axtraceactive)
        self.__active = active
