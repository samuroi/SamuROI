import numpy

import matplotlib

from PyQt4 import QtCore, QtGui

from .canvasbase import CanvasBase


class FrameCanvas(CanvasBase):
    """Plot the actual 2D frame of data with all mask artists and the overlay"""

    def __init__(self, segmentation, selectionmodel):
        # initialize the canvas where the Figure renders into
        super(FrameCanvas, self).__init__()

        self.segmentation = segmentation
        self.selectionmodel = selectionmodel
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
        self.segmentation.active_frame_changed.append(self.on_active_frame_cahnged)

        # connect to selection model
        self.selectionmodel.selectionChanged.connect(self.on_selection_changed)

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

    def on_selection_changed(self, selected, deselected):
        for range in deselected:
            for index in range.indexes():
                item = index.internalPointer()
                # the selection could also be a whole tree of e.g. BranchMasks
                if hasattr(item, "mask"):
                    artist = self.get_artist(item.mask)
                    artist.selected = False
        for range in selected:
            for index in range.indexes():
                item = index.internalPointer()
                if hasattr(item, "mask"):
                    artist = self.get_artist(item.mask)
                    artist.selected = True
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

    def on_active_frame_cahnged(self):
        self.frameimg.set_data(self.segmentation.data[..., self.segmentation.active_frame])
        self.draw()

    def onpick(self, event):
        with self.draw_on_exit():
            # get the mask from the event
            mask = event.artist.mask
            # get the model underlying the selection
            model = self.selectionmodel.model()
            # get the model tree item for the mask
            treeitem = model.mask2roitreeitem[mask]

            # if shift key is not pressed clear selection
            if not (event.guiEvent.modifiers() and QtCore.Qt.ShiftModifier):
                self.selectionmodel.clear()
            self.selectionmodel.select(model.createIndex(treeitem.parent().row(treeitem), 0, treeitem),
                                       QtGui.QItemSelectionModel.Select)


class FrameWidget(QtGui.QWidget):
    def __init__(self, parent, segmentation, selectionmodel):
        super(FrameWidget, self).__init__(parent)

        self.segmentation = segmentation

        # create a vertical box layout widget
        self.vbl = QtGui.QVBoxLayout()

        self.frame_canvas = FrameCanvas(segmentation, selectionmodel)
        self.vbl.addWidget(self.frame_canvas)

        from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
        self.toolbar_navigation = NavigationToolbar2QT(self.frame_canvas, self, coordinates=False)

        self.frame_slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(self.segmentation.data.shape[2])
        self.frame_slider.setTickInterval(1)
        self.frame_slider.setSingleStep(1)
        self.frame_slider.setPageStep(self.segmentation.data.shape[2] / 10)
        self.frame_slider.valueChanged.connect(self.on_slider_changed)

        self.toollayout = QtGui.QHBoxLayout()

        self.toollayout.addWidget(self.toolbar_navigation)
        self.toollayout.addWidget(self.frame_slider)

        self.vbl.addLayout(self.toollayout)
        self.setLayout(self.vbl)

    def on_slider_changed(self, value):
        self.segmentation.active_frame = value
