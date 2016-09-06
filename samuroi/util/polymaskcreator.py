from collections import namedtuple

from .maskcreator import MaskCreator
from ..masks.polygon import PolygonMask


class PolyMaskCreator(MaskCreator):
    """Manages the interactive creation of polygon masks."""

    Status = namedtuple('Status', ['x', 'y', 'line'])

    @MaskCreator.enabled.setter
    def enabled(self, e):
        """Extend the active setter of MaskCreator to also remove any artists if deactivated"""
        # call base class property setter
        MaskCreator.enabled.fset(self, e)
        # handle own derived stuff
        if self.status is not None:
            self.status.line.remove()
            self.update()
            self.status = None

    def __init__(self, axes, canvas, update, notify, enabled=False):
        """
            Arguments:
                axes, the axes where the interactive creation takes place
                canvas, the figure canvas, required to connec to signals
                update, a callable which will be called after adding a corner to the currently created polygon
                notify, a callable that will get evoked with the outline of a finished polygon.
                enabled, should mask creation be enabled from the begininig (default False)
        """
        # assign attribute bevore base class constructor call, since the base class will call the enable slot
        self.status = None
        super(PolyMaskCreator, self).__init__(axes=axes,
                                              canvas=canvas,
                                              update=update,
                                              notify=notify,
                                              enabled=enabled)

    def onclick(self, event):
        if self.status is None:
            line, = self.axes.plot([], [], lw=3, scalex=False, scaley=False)
            self.status = self.Status(x=[], y=[], line=line)

        self.status.x.append(event.xdata)
        self.status.y.append(event.ydata)
        self.status.line.set_data(self.status.x, self.status.y)
        self.update()

    def onkey(self, event):
        if self.status is None or event.key != 'enter':
            return

        self.status.x.append(self.status.x[0])
        self.status.y.append(self.status.y[0])
        self.status.line.set_data(self.status.x, self.status.y)
        self.status.line.remove()

        # shift everything by 0.5 because pixels will be centered around 0
        import numpy
        corners = numpy.column_stack([self.status.x, self.status.y]) + 0.5
        self.update()
        self.status = None
        # set status to none before notify, because notify might disable the creator
        self.notify(PolygonMask(outline=corners))
