import numpy

import matplotlib

from PyQt4 import QtCore, QtGui

from .canvasbase import CanvasBase


class TraceCanvas(CanvasBase):
    """Plot a set of traces for a selection defined by a QtSelectionModel"""

    def __init__(self, segmentation, selectionmodel):
        # initialize the canvas where the Figure renders into
        super(TraceCanvas, self).__init__()

        self.segmentation = segmentation
        self.selectionmodel = selectionmodel

        # a dictionary mapping from mask to matplotlib line artist
        self.__traces = {}

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

    def on_selection_changed(self, selected, deselected):
        for range in deselected:
            for index in range.indexes():
                item = index.internalPointer()
                # the selection could also be a whole tree of e.g. BranchMasks
                if hasattr(item, "mask") and item.mask in self.__traces:
                    # remove the artist
                    self.__traces[item.mask].remove()
                    del self.__traces[item.mask]
        for range in selected:
            for index in range.indexes():
                item = index.internalPointer()
                if hasattr(item, "mask"):
                    tracedata = item.mask(self.segmentation.data, self.segmentation.overlay)
                    line, = self.axes.plot(tracedata)
                    # put a handle of the mask on the artist
                    line.mask = item.mask
                    self.__traces[item.mask] = line
        self.draw()

    def on_data_changed(self):
        raise NotImplementedError()

    def on_overlay_changed(self):
        raise NotImplementedError()

    def on_active_frame_cahnged(self):
        raise NotImplementedError()

    def onpick(self, event):
        return
        # for now, do nothing, since if we change the selection from here, this will feedback into our own
        # on_selection_change and remove items we clicked on.
        # with self.draw_on_exit():
        #     # get the mask from the event
        #     mask = event.artist.mask
        #     # get the model underlying the selection
        #     model = self.selectionmodel.model()
        #     # get the model tree item for the mask
        #     treeitem = model.mask2roitreeitem[mask]
        #
        #     # if shift key is not pressed clear selection
        #     if not (event.guiEvent.modifiers() and QtCore.Qt.ShiftModifier):
        #         self.selectionmodel.clear()
        #     self.selectionmodel.select(model.createIndex(treeitem.parent().row(treeitem), 0, treeitem),
        #                                QtGui.QItemSelectionModel.Select)


class TraceDockWidget(QtGui.QDockWidget):
    def __init__(self, name, parent, segmentation, selectionmodel):
        super(TraceDockWidget, self).__init__(name, parent)

        self.tracewidget = TraceCanvas(segmentation=segmentation, selectionmodel=selectionmodel)

        from PyQt4 import QtCore
        from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
        self.toolbar_navigation = NavigationToolbar2QT(self.tracewidget, self, coordinates=False)
        self.toolbar_navigation.setOrientation(QtCore.Qt.Vertical)
        self.toolbar_navigation.setFloatable(True)

        self.widget = QtGui.QWidget()
        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.toolbar_navigation)
        self.layout.addWidget(self.tracewidget)

        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)
