import numpy
from collections import namedtuple

from .maskcreator import MaskCreator

from ..masks.pixel import PixelMask


class PixelMaskCreator(MaskCreator):
    Status = namedtuple('Status', ['x', 'y', 'scatter'])

    @MaskCreator.enabled.setter
    def enabled(self, e):
        """Extend the active setter of MaskCreator to also remove any artists if deactivated"""
        # call base class property setter
        MaskCreator.enabled.fset(self, e)
        # handle own derived stuff
        if self.status is not None:
            self.status.scatter.remove()
            self.update()
            self.status = None

    def __init__(self, axes, canvas, update, notify, enabled=False):
        """
            Arguments:
                axes, the axes where the interactive creation takes place
                canvas, the figure canvas, required to connec to signals
                update, a callable which will be called after adding a pixel to the current mask.
                notify, a callable that will get evoked with the coordinates of all pixels of a finished mask.
                enabled, should mask creation be enabled from the begininig (default False)
        """
        self.status = None
        super(PixelMaskCreator, self).__init__(axes=axes,
                                               canvas=canvas,
                                               update=update,
                                               notify=notify,
                                               enabled=enabled)

    def __contains(self, x, y):
        if x in self.status.x:
            i = self.status.x.index(x)
            return self.status.y[i] == y
        return False

    def onclick(self, event):
        if self.status is None:
            scatter = self.axes.scatter([], [], marker='x')
            self.status = self.Status(x=[], y=[], scatter=scatter)
        x, y = int(round(event.xdata)), int(round(event.ydata))
        # check if we already got the point in the list, if so, remove it
        if self.__contains(x, y):
            # erase element by index from both lists
            i = self.status.x.index(x)
            self.status.x[i:i + 1] = []
            self.status.y[i:i + 1] = []
        else:
            self.status.x.append(x)
            self.status.y.append(y)
        self.status.scatter.set_offsets(numpy.array([self.status.x, self.status.y]).T)
        self.update()

    def onkey(self, event):
        if self.status is None or event.key != 'enter':
            return

        self.status.scatter.remove()
        x, y = self.status.x, self.status.y
        self.update()
        self.status = None
        # set status to None bevore notify, because the notify callback might disable the creator
        self.notify(PixelMask(x,y))
