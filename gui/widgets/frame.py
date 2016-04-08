import numpy

import matplotlib

from PyQt4 import QtCore

from .canvasbase import CanvasBase


class FrameCanvas(CanvasBase):
    """Plot the actual 2D frame of data with all mask artists and the overlay"""

    def __init__(self, segmentation):
        # initialize the canvas where the Figure renders into
        CanvasBase.__init__(self)

        self.segmentation = segmentation
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

        self.segmentation.masks.added.append(self.on_mask_added)
        self.segmentation.masks.removed.append(self.on_mask_removed)
        self.segmentation.overlay_changed.append(self.on_overlay_changed)
        self.segmentation.data_changed.append(self.on_data_changed)
        self.segmentation.selection.added.append(self.on_selection_added)
        self.segmentation.selection.removed.append(self.on_selection_removed)

        self.mpl_connect('pick_event', self.onpick)

    def get_artist(self, mask):
        count = sum(1 for artist in self.axes.artists if artist.mask is mask)
        if count != 1:
            raise Exception("Count = " + str(count))
        # find the artist associated with the mask
        return next(artist for artist in self.axes.artists if artist.mask is mask)

    @property
    def rgba_overlay(self):
        # update overlay image
        overlay = numpy.zeros(shape=self.segmentation.meandata.shape + (4,), dtype=float)
        overlay[..., 3] = numpy.logical_not(self.segmentation.overlay)
        return overlay

    def on_selection_added(self, mask):
        artist = self.get_artist(mask)
        artist.selected = True
        self.draw()

    def on_selection_removed(self, mask):
        artist = self.get_artist(mask)
        artist.selected = False
        self.draw()

    def on_data_changed(self):
        raise NotImplementedError()

    def on_overlay_changed(self):
        self.overlayimg.set_data(self.rgba_overlay)
        self.draw()

    def on_mask_added(self, mask):
        # create an artist based on the type of roi
        from ...artists import create_artist
        artist = create_artist(mask)
        self.axes.add_artist(artist)
        if hasattr(mask, "changed"):
            mask.changed.append(self.on_mask_changed)
        self.draw()

    def on_mask_removed(self, mask):
        for artist in self.axes.artists:
            if artist.mask is mask:
                artist.remove()
                self.draw()

    def on_mask_changed(self, mask):
        self.draw()

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

    def onpick(self, event):
        with self.draw_on_exit():
            # TODO add logic for selecting segments
            # if shift key is not pressed clear selection
            if not (event.guiEvent.modifiers() and QtCore.Qt.ShiftModifier):
                self.segmentation.selection.clear()
            self.segmentation.selection.add(event.artist.mask)
