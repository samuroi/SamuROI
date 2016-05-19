from PyQt4 import QtGui

import numpy
from matplotlib.figure import Figure

from .canvasbase import CanvasBase


class LineScanCanvas(CanvasBase):
    """Class to represent the FigureCanvas widget"""

    def __init__(self, segmentation, selectionmodel):
        # initialize the canvas where the Figure renders into
        super(LineScanCanvas, self).__init__()
        self.segmentation = segmentation
        self.selectionmodel = selectionmodel
        self.branch = None
        self.imglinescan = None
        self.scatterevents = None
        self.axes = self.figure.add_subplot(111)
        self.mpl_connect('button_press_event', self.onclick)
        self.axes.set_xlim(0, self.segmentation.data.shape[-1])
        self.axes.autoscale(False, axis='x')
        self.figure.set_tight_layout(True)

        self.segmentation.active_frame_changed.append(self.on_active_frame_change)
        self.segmentation.overlay_changed.append(self.on_overlay_change)
        self.segmentation.data_changed.append(self.on_data_change)

        # cache calculated line scans in dictionary having the branch mask as key
        self.__linescans = {}

    def on_active_frame_change(self):
        if hasattr(self, "active_frame_line"):
            self.active_frame_line.remove()
        self.active_frame_line = self.axes.axvline(x=self.segmentation.active_frame + 0.5, color='black', lw=1.)
        self.draw()

    def on_overlay_change(self):
        self.__linescans.clear()
        # force update
        if self.branch is not None:
            self.redraw()

    def on_data_change(self):
        self.__linescans.clear()
        # force update
        if self.branch is not None:
            self.redraw()

    def set_branch(self, branch):
        if self.branch is branch:
            return
        # disconnect from the old branch
        if self.branch is not None:
            self.branch.changed.remove(self.on_branch_change)

        self.branch = branch
        self.branch.changed.append(self.on_branch_change)
        self.redraw()

    def redraw(self):
        with self.draw_on_exit():
            # remove the old linescan image
            if self.imglinescan is not None:
                self.imglinescan.remove()
                self.imglinescan = None
            if self.scatterevents is not None:
                self.scatterevents.remove()
                self.scatterevents = None

            if len(self.branch.children) > 0:
                tmax = self.segmentation.data.shape[-1]
                nsegments = len(self.branch.children)
                self.imglinescan = self.axes.imshow(self.linescan, interpolation='nearest', aspect='auto',
                                                    cmap='viridis', extent=(0, tmax, nsegments, 0))
                self.axes.set_ylim(nsegments, 0)

                from itertools import cycle
                cycol = cycle('bgrcm').next
                eventsx = []
                eventsy = []
                colors = []
                for i, child in enumerate(self.branch.children):
                    if hasattr(child, "events"):
                        indices = child.events.indices
                        if not hasattr(child, "color"):
                            child.color = cycol()
                        eventsx.append(child.events.indices)
                        eventsy.append(numpy.ones_like(child.events.indices) * (i + 0.5))
                        colors += [child.color for i in child.events.indices]
                if len(colors) > 0:
                    self.scatterevents = self.axes.scatter(numpy.concatenate(eventsx),
                                                           numpy.concatenate(eventsy),
                                                           color=colors)

    def on_branch_change(self, branch):
        """Will be called when the branch masks number of children change."""
        self.redraw()

    @property
    def linescan(self):
        """
        Calculate the trace for all children and return a 2D array aka linescan for that branch roi.
        """
        if self.branch in self.__linescans:
            return self.__linescans[self.branch]
        import numpy
        data = self.segmentation.data
        overlay = self.segmentation.overlay
        self.__linescans[self.branch] = numpy.row_stack((child(data, overlay) for child in self.branch.children))
        return self.__linescans[self.branch]

    def onclick(self, event):
        if self.branch is not None and event.ydata is not None:
            index = int(event.ydata)
            if index < len(self.branch.children):
                # get the model underlying the selection
                model = self.selectionmodel.model()
                # get the model tree item for the selected segment
                treeitem = model.mask2roitreeitem[self.branch.children[index]]

                # clear selection and add the segment
                self.selectionmodel.clear()
                self.selectionmodel.select(model.createIndex(treeitem.parent().row(treeitem), 0, treeitem),
                                           QtGui.QItemSelectionModel.Select)
        if event.xdata is not None:
            self.segmentation.active_frame = event.xdata


class LineScanDockWidget(QtGui.QDockWidget):
    def __init__(self, name, parent, segmentation):
        super(LineScanDockWidget, self).__init__(name, parent)

        self.linescanwidget = LineScanCanvas(segmentation=segmentation, selectionmodel=parent.roiselectionmodel)

        from PyQt4 import QtCore
        from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
        self.toolbar_navigation = NavigationToolbar2QT(self.linescanwidget, self, coordinates=False)
        self.toolbar_navigation.setOrientation(QtCore.Qt.Vertical)
        self.toolbar_navigation.setFloatable(True)

        self.widget = QtGui.QWidget()
        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.toolbar_navigation)
        self.layout.addWidget(self.linescanwidget)

        self.widget.setLayout(self.layout)
        self.setWidget(self.widget)

    def set_branch(self, branch):
        self.linescanwidget.set_branch(branch)
