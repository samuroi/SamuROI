import itertools

from dumb.util import PolyMask

from matplotlib.patches import Polygon

from abc import abstractmethod, abstractproperty
# from  matplotlib.artist import Artist

class MaskArtist(object):
    """
    Base class for rois that allow calculating traces and have an attached matplotlib artists.
    This class handles trace updates, trace plot states, trace holding and the roi artist managment.
    """

    def __init__(self, mask):
        # self.__active = False

        self.mask = mask
        """The underlying mask object."""

        # self.parent = parent
        # """an object that has a axtraceactive attribute defininf the axes where to plot the active traces"""
        # self.holdaxes = []
        # """the list of axes where this roi actually holds a trace"""
        # self.holdlines = {}
        # """a mapping from the axes where the roi holds a trace, to the line artist"""

    @abstractproperty
    def color(self):
        raise NotImplementedError("")

    @abstractproperty
    def selected(self,v):
        raise NotImplementedError("")
    # def applymask(self):
    #     data = self.parent.data
    #     mask = self.parent.mask
    #     return self.mask(data=data, mask=mask)
    #
    # @property
    # def trace(self):
    #     if self not in self.parent.tracecache:
    #         t = self.applymask()
    #         self.parent.tracecache[self] = self.parent.post_apply(t)
    #     return self.parent.tracecache[self]
    #
    # def relim(self, axes):
    #     """recalculate and update the axes limit after adding/removing a line or updating via notify."""
    #     axes.relim()
    #     axes.autoscale(axis='y', tight=True)
    #     mi, ma = axes.get_ylim()
    #     axes.set_ylim(mi - (ma - mi) * 0.1, ma + (ma - mi) * 0.1)

    # @abstractmethod
    # def add(self,axes):
    #     """add the artist to given axes"""
    #     raise NotImplementedError()
    #
    # @abstractmethod
    # def remove(self,axes):
    #     """remove this artist from the given axes"""
    #     raise NotImplementedError()
    #     """remove all artists and traces"""
    #     if hasattr(self, "traceline"):
    #         self.traceline.remove()
    #     for axes, line in self.holdlines.iteritems():
    #         line.remove()
    #         # recalculate the ylim for the remaining lines
    #         self.relim(axes)
    #     if self in self.parent.tracecache:
    #         del self.parent.tracecache[self]

    # def notify(self):
    #     """ this method is supposed to be called when the trace data has changed."""
    #     # update the trace of active line
    #     if hasattr(self, "traceline"):
    #         trace = self.trace
    #         x, _ = self.traceline.get_data()
    #         self.traceline.set_data(x, trace)
    #
    #     # update the holded traces
    #     for axes, line in self.holdlines.iteritems():
    #         x, _ = line.get_data()
    #         line.set_data(x, self.trace)
    #         self.relim(axes)

    # def toggle_hold(self, ax):
    #     """
    #         Plot the trace on axes even if the roi is not active.
    #     """
    #     if ax in self.holdaxes:
    #         self.holdlines[ax].remove()
    #         del self.holdlines[ax]
    #         self.holdaxes.remove(ax)
    #     else:
    #         self.holdaxes.append(ax)
    #         line, = ax.plot(self.trace, color=self.color, picker=5)
    #         line.roi = self
    #         self.holdlines[ax] = line
    #     # because we have added/removed a line from the holdaxes, we need to relimit the axes
    #     self.relim(ax)
    #
    # @trace.deleter
    # def trace(self):
    #     if self in self.parent.tracecache:
    #         del self.parent.tracecache[self]
    #
    # @property
    # def active(self):
    #     return self.__active
    #
    # @active.setter
    # def active(self, active):
    #     if self.active == active:
    #         return
    #     if active:
    #         self.traceline, = self.parent.axtraceactive.plot(self.trace, color=self.color)
    #     else:
    #         if hasattr(self, "traceline") and self.traceline in self.parent.axtraceactive.lines:
    #             self.traceline.remove()
    #             del self.traceline
    #     self.relim(self.parent.axtraceactive)
    #     self.__active = active
