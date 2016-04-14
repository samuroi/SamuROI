from PyQt4 import QtGui

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas


class LineScanCanvas(FigureCanvas):
    """Class to represent the FigureCanvas widget"""

    def __init__(self, segmentation):
        # initialize the canvas where the Figure renders into
        FigureCanvas.__init__(self, Figure())
        self.segmentation = segmentation
        self.branch = None
        self.imglinescan = None
        self.axes = self.figure.add_subplot(111)
        self.mpl_connect('button_press_event', self.onclick)

    def on_active_frame_change(self):
        if hasattr(self, "active_frame_line"):
            self.active_frame_line.remove()
        self.active_frame_line = self.axes.axvline(x=self.segmentation.active_frame, color='black', lw=1.)
        self.draw()

    def set_branch(self, branch):
        # disconnect from the old branch
        if self.branch is not None:
            self.branch.changed.remove(self.on_branch_change)

        # remove the old linescan image
        if self.imglinescan is not None:
            self.imglinescan.remove()

        self.branch = branch
        self.branch.changed.append(self.on_branch_change)

        if len(self.branch.children) > 0:
            tmax = self.segmentation.data.shape[-1]
            nsegments = len(self.branch.children)
            self.imglinescan = self.axes.imshow(self.linescan, interpolation='nearest', aspect='auto',
                                                cmap='viridis', extent=(0, tmax, nsegments, 0))
            self.axes.set_ylim(nsegments, 0)
            self.draw()

    def on_branch_change(self, branch):
        """Will be called when the branch masks number of children change."""
        if self.imglinescan is None:
            # dirty, but ok, this will create the line scan if the branch has children
            self.set_branch(branch)
        else:
            self.imglinescan.set_data(self.linescan)
            tmax = self.segmentation.data.shape[-1]
            nsegments = len(self.branch.children)
            self.imglinescan.set_extent((0, tmax, nsegments, 0))
            self.axes.set_ylim(nsegments, 0)
            self.draw()

    @property
    def linescan(self):
        """
        Calculate the trace for all children and return a 2D array aka linescan for that branch roi.
        """
        import numpy
        data = self.segmentation.data
        overlay = self.segmentation.overlay
        return numpy.row_stack((child(data, overlay) for child in self.branch.children))

    def onclick(self, event):
        if self.branch is not None and event.ydata is not None:
            index = int(event.ydata)
            if index < len(self.branch.children):
                self.segmentation.selection.clear()
                self.segmentation.selection.add(self.branch.children[index])


class LineScanDockWidget(QtGui.QDockWidget):
    def __init__(self, name, parent, segmentation):
        super(LineScanDockWidget, self).__init__(name, parent)

        self.linescanwidget = LineScanCanvas(segmentation=segmentation)
        self.setWidget(self.linescanwidget)

    def set_branch(self, branch):
        self.linescanwidget.set_branch(branch)
