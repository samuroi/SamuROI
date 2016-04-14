import numpy

from PyQt4 import QtCore, QtGui

from contextlib import contextmanager

from ..segmentationderived import SegmentationExtension


class DendriteSegmentationTool(QtGui.QMainWindow):
    """
    The main class that is doing the event handling, organizes the gui and puts together the plot.
    """

    class TraceCache(dict):
        """
        notify all rois with cached traces to update their plots on cach clearing.
        """

        def clear(self):
            rois = self.keys()
            dict.clear(self)
            for roi in rois:
                roi.notify()

    def on_data_changed(self, d):
        # force recalculation of traces
        with self.disable_draw():
            self.tracecache.clear()
            # set proper ylimit for axtraceactive and axtracehold
            for ax in [self.axtraceactive] + self.axtracehold:
                if len(ax.lines) <= 1: continue  # skip axes if it only contains one line (the frame marker)
                ymin, ymax = 0, 0
                for l in ax.lines:
                    x, y = l.get_data()
                    # filter out the vertical frame marker line
                    if len(x) <= 2: continue
                    ymin = min(numpy.min(y), ymin)
                    ymax = max(numpy.max(y), ymax)
                ax.set_ylim(ymin * 0.95, ymax * 1.05)
        self.fig.canvas.draw()

    def on_overlay_changed(self, m):
        # force recalculation of traces
        with self.disable_draw():
            self.tracecache.clear()
            # set proper ylimit for axtraceactive and axtracehold
            for ax in [self.axtraceactive] + self.axtracehold:
                if len(ax.lines) <= 1: continue  # skip axes if it only contains one line (the frame marker)
                ymin, ymax = 0, 0
                for l in ax.lines:
                    x, y = l.get_data()
                    # filter out the vertical frame marker line
                    if len(x) <= 2: continue
                    ymin = min(numpy.min(y), ymin)
                    ymax = max(numpy.max(y), ymax)
                ax.set_ylim(ymin * 0.95, ymax * 1.05)
        self.fig.canvas.draw()

    def split_segment(self, segment, parts=2):
        """Split the given segment in to equal parts."""
        # segment = self.active_segment if segment is None else segment

        # there might be no active segment
        if segment is None:
            return

        # get the index of the old segment in the parents child list
        i = segment.parent.children.index(segment)

        segment.split(nsegments=parts)
        if segment.parent.active:
            self.active_segment = segment.parent.children[i]

    def join_segments(self, segment, next=True):
        """
        Join two segments into one. Arguments:
            segment: A segment of any branch. Defaults to the active segment.
            next:    True or False, denote whether to join the segment with the preceeding or succeeding one.
        """
        # segment = self.active_segment if segment is None else segment

        # there might be no active segment
        if segment is None:
            return

        # create and retrieve the new segment
        joined = segment.join(next=next)

        # make the new segment active
        if segment.parent.active:
            self.active_segment = joined

    @contextmanager
    def disable_draw(self):
        # store the original draw method
        draw = self.fig.canvas.draw

        def noop(*args):
            pass

        # override the draw method as noop
        self.fig.canvas.draw = noop

        # yield and run code in context
        yield

        # restore the original behaviour of draw
        self.fig.canvas.draw = draw

    def __init__(self, data, mean=None, pmin=10, pmax=99):
        """
        Create and show the gui for data analysis.
        Args:
            data:  The 3D dataset
            swc:   SWC File that allows looping over branches.
            mean: Background image. Defaults to data.mean(axis = -1)
            pmin,pmax: Percentiles for color range. I.e. the color range for mean and data will start at pmin %
                           and reach up to pmax %. Defaults to (10,99)
        """
        QtGui.QMainWindow.__init__(self)

        self.segmentation = SegmentationExtension(data, mean)

        # set window title
        self.setWindowTitle("DendriteSegmentationTool")
        # instantiate a widget, it will be the main one
        self.setCentralWidget(QtGui.QWidget(self))
        # create a vertical box layout widget
        self.vbl = QtGui.QVBoxLayout(self.centralWidget())

        # ntb = NavigationToolbar(qmc, self.main_widget)

        # create widget for frame
        from .widgets.frame import FrameCanvas
        self.frame_canvas = FrameCanvas(segmentation=self.segmentation)
        self.vbl.addWidget(self.frame_canvas)

        # self.tracecache = DendriteSegmentationTool.TraceCache()
        # """dictionary that notifies artists on cache clear."""
        #
        # self.mask_artists = dict()
        # """a mapping from mask to artist"""
        #
        # self.mask_selection = MaskSelection(artists=self.mask_artists)
        # """A set of all selected masks. To change selection state, just add/remove masks to/from the set."""
        #

        #
        # self._setup_figure()
        self._setup_toolbars()

        # self.active_frame = 0

        # self.colors = ['#CC0099', '#CC3300', '#99CC00', '#00FF00', '#006600', '#999966']
        # self.colorcycle = itertools.cycle(self.colors)

        # connect gui update slots to data change signals
        # self.masks.added.append(self.on_mask_added)
        # self.masks.removed.append(self.on_mask_removed)
        # self.overlay_changed.append(self.on_overlay_changed)
        # self.data_changed.append(self.on_data_changed)
        # self.postprocessor_changed.append(self.on_postprocessor_changed)

        # self.fig.canvas.mpl_disconnect(self.fig.canvas.manager.key_press_handler_id)
        # self.fig.canvas.mpl_connect('key_press_event', noraise(self.onkey))

        from .filemenu import FileMenu
        menubar = self.menuBar()
        self.file_menu = FileMenu(app=self)
        menubar.addMenu(self.file_menu)

        from .widgets.linescan import LineScanDockWidget
        self.linescandockwidget = LineScanDockWidget("Linescan", parent=self, segmentation=self.segmentation)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.linescandockwidget)

        from .roitree import RoiTreeWidget
        roitreedockwidget = QtGui.QDockWidget("Treeview", parent=self)
        roitreewidget = RoiTreeWidget(parent=roitreedockwidget, masks=self.segmentation.masks,
                                      selection=self.segmentation.selection)
        roitreedockwidget.setWidget(roitreewidget)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, roitreedockwidget)

        self.segmentation.selection.added.append(self.on_selection_change)
        self.segmentation.selection.removed.append(self.on_selection_change)

    def on_selection_change(self, mask):
        """
        When the selection is either a single branch, or a set of segments from only one branch,
        then update the linescan widget.
        """
        from ..masks.branch import BranchMask
        from ..masks.segment import SegmentMask
        branches = set()
        if BranchMask in self.segmentation.selection.types():
            for branch in self.segmentation.selection[BranchMask]:
                branches.add(branch)

        # add all segment parents to the branch set
        if SegmentMask in self.segmentation.selection.types():
            for segment in self.segmentation.selection[SegmentMask]:
                branches.add(segment.parent)

        if len(branches) == 1:
            self.linescandockwidget.set_branch(branches.pop()   )

    def _setup_toolbars(self):
        # self.toolbar_navigation = self.fig.canvas.manager.toolbar

        from .toolbars import NavigationToolbar
        self.toolbar_branch = NavigationToolbar(parent=self)
        self.addToolBar(self.toolbar_branch)

        from .toolbars import MaskToolbar
        self.toolbar_mask = MaskToolbar(parent=self)
        self.addToolBar(self.toolbar_mask)

        from .toolbars import SplitJoinToolbar
        self.toolbar_splitjoin = SplitJoinToolbar(parent=self)
        self.addToolBar(self.toolbar_splitjoin)

        from .toolbars import ManageRoiToolbar
        self.toolbar_createroi = ManageRoiToolbar(parent=self)
        self.addToolBar(self.toolbar_createroi)
        #
        # from .toolbars import TraceHoldToolbar
        # self.toolbar_tracehold = TraceHoldToolbar(app=self)
        # self.toolbar_tracehold.holdChanged.connect(self.toggle_hold)
        # self.addToolBar(self.toolbar_tracehold)
        #
        # from .toolbars import PostTraceToolbar
        # self.toolbar_postprocess = PostTraceToolbar(app=self)
        # self.toolbar_postprocess.revalidate.connect(self.toggle_filter)
        # self.addToolBar(self.toolbar_postprocess)

    def post_apply(self, trace):
        """
        This is a callback function for the rois. It gets called after trace generation and is responsible for all
        post processing of traces.
        Args:
            trace: The raw trace of the roi
        Returns:
            trace: A postprocessed trace of the roi

        """

        import numpy
        import scipy.signal
        if self.toolbar_postprocess.toggle_detrend.isChecked():
            if not numpy.isinf(trace).any() and not numpy.isnan(trace).any():
                trace = scipy.signal.detrend(trace)
        if self.toolbar_postprocess.toggle_smoothen.isChecked():
            N = self.toolbar_postprocess.spin_smoothen.value()
            trace = numpy.convolve(trace, numpy.ones(shape=N), mode='same') / N
        return trace

    def toggle_filter(self):
        with self.disable_draw():
            self.tracecache.clear()
        self.fig.canvas.draw()

    def toggle_hold(self, ax):
        if type(ax) is int:
            ax = self.axtracehold[ax]

        roi = self.active_roi if self.active_segment is None else self.active_segment
        if roi is not None:
            roi.toggle_hold(ax)
            self.fig.canvas.draw()

    def onkey(self, event):
        if event.inaxes in self.timeaxes and event.key == ' ':
            self.active_frame = int(event.xdata)
        if event.key == '+' and not self.toolbar_createroi.branchmask_creator.enabled:
            self.threshold = self.threshold * 1.05
        if event.key == '-' and not self.toolbar_createroi.branchmask_creator.enabled:
            self.threshold = self.threshold / 1.05
        if event.key == 'm':
            self.toggle_overlay()
