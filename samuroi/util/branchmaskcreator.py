from matplotlib.patches import Polygon, Circle

from .maskcreator import MaskCreator
from ..masks.branch import BranchMask
from ..masks.circle import CircleMask
from ..util.branch import Branch


class BranchMaskCreator(MaskCreator):
    default_radius = 5.

    @MaskCreator.enabled.setter
    def enabled(self, e):
        """Extend the active setter of MaskCreator to also remove any artists if deactivated"""
        # call base class property setter
        MaskCreator.enabled.fset(self, e)
        # handle own derived stuff
        if self.artist is not None:
            self.artist.remove()
            self.artist = None
            self.x, self.y, self.r = [], [], []
            self.update()

    def __init__(self, axes, canvas, update, notify, enabled=False):
        """
            Arguments:
                axes, the axes where the interactive creation takes place
                canvas, the figure canvas, required to connec to signals
                update, a callable which will be called after adding a pixel to the current mask.
                notify, a callable that will get evoked with the coordinates of all pixels of a finished mask.
                enabled, should mask creation be enabled from the begininig (default False)
        """
        self.artist = None
        # container for x,y and radius values
        self.x, self.y, self.r = [], [], []
        super(BranchMaskCreator, self).__init__(axes=axes,
                                                canvas=canvas,
                                                update=update,
                                                notify=notify,
                                                enabled=enabled)

    def onclick(self, event):
        self.x.append(event.xdata)
        self.y.append(event.ydata)
        # reuse last radius for consecutive segments
        if len(self.r) > 0:
            self.r.append(self.r[-1])
        else:
            self.r.append(BranchMaskCreator.default_radius)

        self.__update_artist()

        self.update()

    def __update_artist(self):
        # check if this is the first point of a branch
        if self.artist is None:
            self.artist = Circle([self.x[0], self.y[0]], radius=self.r[0], fill=False,
                                 lw=2, color='red')
            self.axes.add_artist(self.artist)
        elif len(self.x) == 0:
            self.artist.remove()
            self.artist = None
        elif len(self.x) == 1:
            self.artist.remove()
            self.artist = Circle([self.x[0], self.y[0]], radius=self.r[0], fill=False,
                                 lw=2, color='red')
            self.axes.add_artist(self.artist)
        # change from circle to polygon if more than 1 points are available
        elif len(self.x) == 2:
            self.artist.remove()
            branch = Branch(x=self.x, y=self.y, z=[0 for i in self.x], r=self.r)
            self.artist = Polygon(branch.outline, fill=False, color='red', lw=2)
            self.axes.add_artist(self.artist)
        else:
            assert (len(self.x) > 2)
            branch = Branch(x=self.x, y=self.y, z=[0 for i in self.x], r=self.r)
            self.artist.set_xy(branch.outline)

    def onkey(self, event):
        if self.artist is not None:
            if event.key == '+':
                self.r[-1] = self.r[-1] + 1
                self.__update_artist()
                self.update()
            elif event.key == '-':
                self.r[-1] = self.r[-1] - 1
                self.__update_artist()
                self.update()
            elif event.key == 'z':
                print event
                print dir(event)
                self.r = self.r[:-1]
                self.x = self.x[:-1]
                self.y = self.y[:-1]
                self.__update_artist()
                self.update()
            elif event.key == 'enter':
                self.artist.remove()
                self.update()
                self.artist = None
                if len(self.x) == 1:
                    # shift by 0.5 to compensate for pixel offset in imshow
                    mask = CircleMask(center=[self.x[0] + 0.5, self.y[0] + 0.5], radius=self.r[0])
                else:
                    import numpy
                    dtype = [('x', float), ('y', float), ('z', float), ('radius', float)]
                    x = numpy.array(self.x) + 0.5
                    y = numpy.array(self.y) + 0.5
                    z = [0 for i in self.x]
                    r = self.r
                    data = numpy.rec.fromarrays([x, y, z, r], dtype=dtype)
                    # shift by 0.5 to compensate for pixel offset in imshow
                    mask = BranchMask(data=data)
                self.x, self.y, self.r = [], [], []
                self.notify(mask)
                self.enabled = False
