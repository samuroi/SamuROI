import numpy

from epo.maskcreator import MaskCreator
from collections import namedtuple

class PixelMaskCreator(MaskCreator):

    Status = namedtuple('Status',['x','y','scatter'])

    @MaskCreator.enabled.setter
    def enabled(self, e):
        """Extend the active setter of MaskCreator to also remove any artists if deactivated"""
        # call base class property setter
        MaskCreator.enabled.fset(self,e)
        # handle own derived stuff
        if self.status is not None:
            self.status.line.remove()
            self.update()
            self.status = None

    def __init__(self, axes, canvas, update, notify, enabled = False):
        """
            Arguments:
                axes, the axes where the interactive creation takes place
                canvas, the figure canvas, required to connec to signals
                update, a callable which will be called after adding a pixel to the current mask.
                notify, a callable that will get evoked with the coordinates of all pixels of a finished mask.
                enabled, should mask creation be enabled from the begininig (default False)
        """
        self.status = None
        super(PixelMaskCreator,self).__init__(axes = axes,
                                              canvas = canvas,
                                              update = update,
                                              notify = notify,
                                              enabled = enabled)



    def onclick(self,event):
        if self.status is None:
            scatter = self.axes.scatter([],[],marker = 'x')
            self.status = self.Status(x = [], y = [], scatter = scatter)

        self.status.x.append(int(round(event.xdata)))
        self.status.y.append(int(round(event.ydata)))
        self.status.scatter.set_offsets(numpy.array([self.status.x,self.status.y]).T)
        self.update()

    def onkey(self,event):
        if self.status is None or event.key != 'enter':
            return

        self.status.scatter.remove()
        self.notify(self.status.x, self.status.y)
        self.update()
        self.status = None
