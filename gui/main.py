import numpy
# import matplotlib
import itertools

from PyQt4 import QtCore, QtGui

# import matplotlib.pyplot as plt
# import matplotlib.gridspec as gridspec
#
from contextlib import contextmanager

from dumb.util import noraise, bicyclelist

from ..segmentation import Segmentation

# don't inherit from built in set, cause of some issues
from collections import MutableSet


class MaskSelection(MutableSet):
    """
    Use generic mixin functions. hence we only need to reimplement:
        __contains__, __iter__, __len__, add(), and discard().
    """

    def __init__(self, artists):
        """
            artists: a dict that provides mapping from mask to artist
        """
        self.__masks = set()
        self.__artists = artists

    def add(self, mask):
        artist = self.__artists[mask]
        artist.active = True
        return self.__masks.add(self, artist)

    def discard(self, mask):
        if mask in self.__masks:
            artist = self.__artists[mask]
            artist.active = False
        return self.__masks.discard(mask)

    def __contains__(self, mask):
        return mask in self.__masks

    def __iter__(self):
        return self.__masks.__iter__()

    def __len__(self):
        return len(self.__masks)


class SelectionBicycle(bicyclelist):
    """
    Calls to next, prev and cur will invalidate the selection and set the respective element as selected
    """

    def __init__(self, selection):
        super(bicyclelist, self).__init__()
        self.__selection = selection

    def next(self):
        item = bicyclelist.next(self)
        self.__selection.clear()
        self.__selection.add(item)
        return item

    def cur(self):
        item = bicyclelist.cur(self)
        self.__selection.clear()
        self.__selection.add(item)
        return item

    def prev(self):
        item = bicyclelist.prev(self)
        self.__selection.clear()
        self.__selection.add(item)
        return item


from PyQt4 import QtGui


class DendriteSegmentationTool(QtGui.QMainWindow, Segmentation):
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

    def on_postprocessor_changed(self):
        self

    def on_mask_added(self, mask):
        if mask in self.mask_artists:
            raise Exception("The given roi <{}> is already managed by this Segmentation.".format(mask))
        # create an artist based on the type of roi
        from ..artists import create_artist as Artist

        artist = self.mask_artists[mask] = Artist(mask, self)

        # add the artist to cyclic lists which will allow easy prev/next
        self.__selection_cycles.setdefault(type(mask), SelectionBicycle(selection=self.mask_selection)).append(mask)
        self.__selection_cycles["all"].append(mask)

    def on_mask_removed(self, mask):
        if mask not in self.mask_artists:
            raise Exception("The given roi <{}> is not managed by this Segmentation.".format(mask))
        artist = self.mask_artists[mask]
        del self.mask_artists[mask]
        artist.remove()

        # remove the artist from the cyclic lists
        self.__selection_cycles[type(mask)].remove(mask)
        self.__selection_cycles["all"].remove(mask)

    def on_roi_changed(self, roi):
        pass

    @property
    def branch_cycle(self):
        from ..masks.branch import BranchMask
        return self.__selection_cycles[BranchMask]

    @property
    def polygon_cycle(self):
        from ..masks.polygon import PolygonMask
        return self.__selection_cycles[PolygonMask]

    @property
    def pixel_cycle(self):
        from ..masks.pixel import PixelMask
        return self.__selection_cycles[PixelMask]

    @property
    def circle_cycle(self):
        from ..masks.circle import CircleMask
        return self.__selection_cycles[CircleMask]

    @property
    def artist_cycle(self):
        return self.__selection_cycles["all"]

    # def next_segment(self):
    #     if self.active_branch is not None:
    #         self.active_segment = self.active_branch.next_segment()
    #
    # def previous_segment(self):
    #     if self.active_branch is not None:
    #         self.active_segment = self.active_branch.previous_segment()

    @property
    def active_frame(self):
        return self.__active_frame

    @active_frame.setter
    def active_frame(self, f):
        with self.disable_draw():
            if not 0 <= f < self.data.shape[2]:
                raise Exception("Frame needs to be in range [0,{}]".format(self.data.shape[2]))

            self.__active_frame = f

            # remove the markers
            if hasattr(self, "_DendriteSegmentationTool__active_frame_lines"):
                for l in self.__active_frame_lines:
                    l.remove()

            # redraw the markers
            self.__active_frame_lines = []
            for ax in self.timeaxes:
                l = ax.axvline(x=f, color='black', lw=1.)
                self.__active_frame_lines.append(l)

        self.fig.canvas.draw()

    def split_branches(self, length):
        with self.disable_draw():
            Segmentation.split_branches(self, length=length)
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
        Segmentation.__init__(self, data=data, mean=mean)
        QtGui.QMainWindow.__init__(self)
        # set window title
        self.setWindowTitle("DendriteSegmentationTool")
        # instantiate a widget, it will be the main one
        self.setCentralWidget(QtGui.QWidget(self))
        # create a vertical box layout widget
        self.vbl = QtGui.QVBoxLayout(self.centralWidget())

        # ntb = NavigationToolbar(qmc, self.main_widget)

        # create widget for frame
        from .widgets.frame import FrameCanvas
        self.frame_canvas = FrameCanvas(segmentation=self)
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
        # self.__selection_cycles = dict()
        # """For each type of mask, hold a bicycle list of masks to cycle through the respective group. Also hold a cycle containing all masks."""
        # self.__selection_cycles["all"] = SelectionBicycle(selection=self.mask_selection)
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
        # self.fig.canvas.mpl_connect('pick_event', noraise(self.onpick))
        # self.fig.canvas.mpl_connect('key_press_event', noraise(self.onkey))

        from .filemenu import FileMenu
        menubar = self.menuBar()
        self.file_menu = FileMenu(app=self)
        menubar.addMenu(self.file_menu)

        from .widgets.linescan import LineScanCanvas
        linescandockwidget = QtGui.QDockWidget("Linescan", parent=self)
        linescanwidget = LineScanCanvas(parent=self)
        linescandockwidget.setWidget(linescanwidget)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, linescandockwidget)

        # from .roitree import RoiTreeWidget
        # roitreedockwidget = QtGui.QDockWidget("Treeview",parent=self)
        # roitreewidget = RoiTreeWidget(parent=roitreedockwidget, rois=self.rois)
        # roitreedockwidget.setWidget(roitreewidget)
        # self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, roitreedockwidget)

        # finally, select first branch
        # self.next_branch()

    def _setup_figure(self):
        self.fig = plt.figure()

        self.gs = gridspec.GridSpec(2, 1, height_ratios=[.3, .7])
        self.axraster = plt.subplot(self.gs[0])
        self.gsl = gridspec.GridSpecFromSubplotSpec(4, 2, subplot_spec=self.gs[1], height_ratios=[.6, 1, 1, 1],
                                                    hspace=0.075)
        self.aximage = plt.subplot(self.gsl[:, 1])
        self.axtraceactive = plt.subplot(self.gsl[0, 0], sharex=self.axraster)
        self.axhold1 = plt.subplot(self.gsl[1, 0], sharex=self.axraster)
        self.axhold2 = plt.subplot(self.gsl[2, 0], sharex=self.axraster)
        self.axhold3 = plt.subplot(self.gsl[3, 0], sharex=self.axraster)

        self.axtracehold = [self.axhold1, self.axhold2, self.axhold3]
        """ a list with the axes where traces can put on hold"""
        self.timeaxes = [self.axtraceactive] + self.axtracehold + [self.axraster]
        """ a list with all axes that have time as x axis"""

        # disable labels in the hold axes two timeaxes and label the active axes
        self.axtraceactive.tick_params(axis='x', labelbottom=False, labeltop=True)

        for ax in self.axtracehold:
            ax.tick_params(axis='x', labelbottom=False)

        for ax in self.timeaxes:
            ax.set_xlim(0, self.data.shape[-1])

    def _setup_toolbars(self):
        # self.toolbar_navigation = self.fig.canvas.manager.toolbar

        from .toolbars import NavigationToolbar
        self.toolbar_branch = NavigationToolbar(app=self)
        self.addToolBar(self.toolbar_branch)

        from .toolbars import MaskToolbar
        self.toolbar_mask = MaskToolbar(frame_canvas=self.frame_canvas)
        self.addToolBar(self.toolbar_mask)

        # from .toolbars import SplitJoinToolbar
        # self.toolbar_splitjoin = SplitJoinToolbar(app=self)
        # self.addToolBar(self.toolbar_splitjoin)
        #
        # from .toolbars import ManageRoiToolbar
        # self.toolbar_createroi = ManageRoiToolbar(app=self)
        # self.addToolBar(self.toolbar_createroi)
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

    def onpick(self, event):
        if event.mouseevent.inaxes is self.aximage:
            roi = event.artist.roi
        elif event.mouseevent.inaxes in [self.axtraceactive] + self.axtracehold and hasattr(event.artist, "roi"):
            roi = event.artist.roi
        else:
            roi = None

        if roi in self.rois:
            self.active_roi = roi
        else:
            for b in self.branchrois:
                if roi in b.children:
                    self.active_segment = roi
