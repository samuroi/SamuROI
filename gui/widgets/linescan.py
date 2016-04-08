from matplotlib.figure import Figure
# import the Qt4Agg FigureCanvas object, that binds Figure to  Qt4Agg backend. It also inherits from QWidget
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

class LineScanCanvas(FigureCanvas):
    """Class to represent the FigureCanvas widget"""

    def __init__(self, parent):
        # initialize the canvas where the Figure renders into
        FigureCanvas.__init__(self, Figure())
        self.parent = parent
        self.branch = None
        self.axes = self.figure.add_subplot(111)
        self.mpl_connect('button_press_event', self.onclick)

    def set_branch(self, branch):
        self.branch = branch

    @property
    def linescan(self):
        """
        Calculate the trace for all children and return a 2D array aka linescan for that branch roi.
        """
        return numpy.row_stack((child.trace for child in self.children))

    def onclick(self, event):
        if self.branch is not None:
            index = int(event.ydata)
            if index < len(self.branch.children):
                self.active_segment = self.active_branch.children[index]