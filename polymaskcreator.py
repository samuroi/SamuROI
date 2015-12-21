from collections import namedtuple

from dumb.util import noraise

class PolyRoiCreator(object):
    """Manages the interactive creation of polygon masks."""

    Status = namedtuple('Status',['x','y','line'])

    @property
    def enabled(self):
        return self.clickslot is not None

    @enabled.setter
    def enabled(self, e):
        """If disabled while creating a mask, mask gets discarded."""
        if not self.enabled and e:
            self.__connect()
        elif self.enabled and not e:
            self.__disconnect()
            if self.status is not None:
                self.status.line.remove()
                self.update()
                self.status = None

    def __init__(self, axes, canvas, update, notify, enabled = False):
        """
            Arguments:
                axes, the axes where the interactive creation takes place
                canvas, the figure canvas, required to connec to signals
                update, a callable which will be called after adding a corner to the currently created polygon
                notify, a callable that will get evoked with the outline of a finished polygon.
                enabled, should mask creation be enabled from the begininig (default False)
        """
        self.axes   = axes
        self.canvas = canvas
        self.status = None
        self.update = update
        self.notify = notify
        self.clickslot = None
        self.keyslot   = None

        # connect slots via property setter
        self.enabled = enabled

    def __connect(self):
        self.clickslot = self.canvas.mpl_connect('button_press_event',self.onclick)
        self.keyslot   = self.canvas.mpl_connect('key_press_event',self.onkey)

    def __disconnect(self):
        if self.keyslot is not None:
            self.canvas.mpl_disconnect(self.clickslot)
            self.canvas.mpl_disconnect(self.keyslot)
            self.keyslot   = None
            self.clickslot = None

    @noraise
    def onclick(self,event):
        # filter out all events of other axes
        if self.axes is not event.inaxes:
            return

        if self.status is None:
            line, = self.axes.plot([],[], lw = 3,scalex = False, scaley = False)
            self.status = self.Status(x = [], y = [], line = line)

        self.status.x.append(event.xdata)
        self.status.y.append(event.ydata)
        self.status.line.set_data(self.status.x,self.status.y)
        self.update()

    @noraise
    def onkey(self,event):
        if self.status is None or event.key != 'enter':
            return

        self.status.x.append(self.status.x[0])
        self.status.y.append(self.status.y[0])
        self.status.line.set_data(self.status.x,self.status.y)
        self.status.line.remove()
        self.notify(self.status.x, self.status.y)
        self.update()
        self.status = None
