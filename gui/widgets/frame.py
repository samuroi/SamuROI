import numpy

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas


class FrameCanvas(FigureCanvas):
    """Plot the actual 2D frame of data with all mask artists and the overlay"""

    def __init__(self, segmentation):
        # initialize the canvas where the Figure renders into
        FigureCanvas.__init__(self, Figure())
        self.segmentation = segmentation
        self.axes = self.figure.add_subplot(111)
        self.__active_frame = None

        pmin, pmax = 10, 99
        vmin, vmax = numpy.percentile(self.segmentation.meandata.flatten(), q=[pmin, pmax])
        self.meanimg = self.axes.imshow(self.segmentation.meandata, cmap=matplotlib.cm.gray,
                                        interpolation='nearest', vmin=vmin, vmax=vmax)

        red_alpha_cm = matplotlib.cm.get_cmap('jet')
        red_alpha_cm._init()
        red_alpha_cm._lut[:, -1] = numpy.linspace(.0, 1.0, red_alpha_cm.N + 3)
        # red_alpha_cm.set_under([0,0,0,0])

        # norm = matplotlib.colors.LogNorm(.001,1.)
        x, y, t = self.segmentation.data.shape
        vmin, vmax = numpy.nanpercentile(self.segmentation.data[..., :min(t / 10, 50)], q=[pmin, pmax])
        norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax, clip=True)
        self.frameimg = self.axes.imshow(self.segmentation.data[..., 0], cmap=red_alpha_cm, norm=norm,
                                         interpolation='nearest')
        self.overlayimg = self.axes.imshow(self.rgba_overlay, interpolation="nearest")
        # disable autoscale on image axes, to avoid rescaling due to additional artists.
        self.axes.set_autoscale_on(False)

        self.figure.colorbar(self.frameimg, ax=self.axes)

    @property
    def rgba_overlay(self):
        # update overlay image
        overlay = numpy.zeros(shape=self.segmentation.meandata.shape + (4,), dtype=float)
        overlay[..., 3] = numpy.logical_not(self.segmentation.overlay)
        return overlay

    def on_data_changed(self, d):
        raise NotImplementedError()

    def on_overlay_changed(self, m):
        self.overlayimg.set_data(self.rgba_overlay)
        self.draw()

    def on_mask_added(self, mask):
        raise NotImplementedError()

    def on_mask_removed(self, mask):
        raise NotImplementedError()

    def on_roi_changed(self, roi):
        raise NotImplementedError()

    @property
    def show_overlay(self):
        return self.overlayimg.get_visible()

    @show_overlay.setter
    def show_overlay(self, v):
        # see if value changed
        b = self.show_overlay
        self.overlayimg.set_visible(v)
        if (b and not v) or (v and not b):
            self.draw()

    def toggle_overlay(self):
        self.show_overlay = not self.show_overlay

    @property
    def active_frame(self):
        return self.__active_frame

    @active_frame.setter
    def active_frame(self, f):
        if not 0 <= f < self.segmentation.data.shape[2]:
            raise Exception("Frame needs to be in range [0,{}]".format(self.segmentation.data.shape[2]))

        self.__active_frame = f
        self.frameimg.set_data(self.segmentation.data[..., f])

        self.draw()
