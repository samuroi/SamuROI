import numpy
import skimage
import matplotlib
import itertools

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from contextlib import contextmanager

import skimage.filters
import skimage.morphology

from dumb.util import noraise

from dumb.util import bicyclelist

from .rois.roi import Roi
from .rois.pixelroi import PixelRoi
from .rois.polyroi import PolygonRoi
from .rois.branchroi import BranchRoi
from .rois.segmentroi import SegmentRoi

from .pixelmaskcreator import PixelMaskCreator
from .polymaskcreator import PolyMaskCreator
from .branchmaskcreator import BranchMaskCreator

from PyQt4 import QtGui


#TODO masks for branches with only one line aka 0 segments aka spines


class DendriteSegmentationTool(object):
    """
    The main class that is doing the event handling, organizes the gui and puts together the plot.
    """
    @property
    def split_length(self):
        return self.split_length_widget.value()

    @split_length.setter
    def split_length(self,v):
        self.split_length_widget.setValue(v)

    @property
    def threshold(self):
        return self.__threshold

    @threshold.setter
    def threshold(self,t):
        with self.disable_draw():
            self.__threshold = t
            elevation_map = skimage.filters.sobel(self.meandata)

            markers = numpy.zeros_like(self.meandata)
            markers[self.meandata < self.threshold] = 1
            markers[self.meandata > self.threshold*1.1] = 2
            segmentation = skimage.morphology.watershed(elevation_map, markers)

            overlay = numpy.zeros(shape = self.meandata.shape + (4,),dtype = float)
            overlay[...,3] = segmentation == 1
            if not hasattr(self,"overlayimg"):
                self.overlayimg = self.aximage.imshow(overlay,interpolation = "nearest")
            else:
                self.overlayimg.set_data(overlay)
            self.mask = segmentation == 2
            # force recalculation of traces
            PolygonRoi.tracecache.clear()
            # set proper ylimit for axtraceactive and axtracehold
            for ax in [self.axtraceactive] + self.axtracehold:
                if len(ax.lines) <= 1: continue # skip axes if it only contains one line (the frame marker)
                ymin,ymax = 0,0
                for l in ax.lines:
                    x,y = l.get_data()
                    # filter out the vertical frame marker line
                    if len(x) <= 2: continue
                    ymin = min(numpy.min(y),ymin)
                    ymax = max(numpy.max(y),ymax)
                ax.set_ylim(ymin*0.95,ymax*1.05)
        self.fig.canvas.draw()

    @property
    def show_overlay(self):
        return self.overlayimg.get_visible()

    @show_overlay.setter
    def show_overlay(self, v):
        # see if value changed
        b = self.show_overlay
        self.overlayimg.set_visible(v)
        self.btn_toggle_mask.setChecked(v)
        if (b and not v) or (v and not b):
            self.fig.canvas.draw()

    def next_branch(self):
        if len(self.branches) > 0:
            self.active_roi = self.branches.next()

    def previous_branch(self):
        if len(self.branches) > 0:
            self.active_roi = self.branches.prev()

    def next_pixelroi(self):
        if len(self.pixelrois) > 0:
            self.active_roi = self.pixelrois.next()

    def next_polyroi(self):
        if len(self.polyrois) > 0:
            self.active_roi = self.polyrois.next()

    def previous_pixelroi(self):
        if len(self.pixelrois) > 0:
            self.active_roi = self.pixelrois.prev()

    def previous_polyroi(self):
        if len(self.polyrois) > 0:
            self.active_roi = self.polyrois.prev()

    def next_segment(self):
         if self.active_branch is not None:
            self.active_roi = self.active_branch.next_segment()

    def previous_segment(self):
        if self.active_branch is not None:
            self.active_roi = self.active_branch.previous_segment()

    @property
    def active_roi(self):
        """
        Return the active roi. This can be any of the following:
         - a branch (if the branch has no segments)
         - a segment of a branch (the corresponding active branch can be obtained by segment.parent)
         - a freehand polygon roi
         - a pixel based roi
         - None
        """
        if not hasattr(self, "_activeroi"):
            self._activeroi = None
        return self._activeroi


    @property
    def active_segment(self):
        if type(self.active_roi) is SegmentRoi:
            return self.active_roi
        else:
            return None

    @property
    def active_branch(self):
        if type(self.active_roi) is BranchRoi:
            return self.active_roi
        elif type(self.active_roi) is SegmentRoi:
            return self.active_roi.parent
        else:
            return None

    @property
    def active_polyroi(self):
        if type(self.active_roi) is PolygonRoi:
            return self.active_roi
        else:
            return None

    @property
    def active_pixelroi(self):
        if type(self.active_roi) is PixelRoi:
            return self.active_roi
        else:
            return None

    @property
    def active_frame(self):
        return self.__active_frame

    @active_roi.setter
    def active_roi(self,p):
        if self.active_roi is p:
            return
        with self.disable_draw():
            # TODO check if p is in any of the roi groups
            before = self.active_roi

            # disable previously active roi
            if self.active_roi is not None:
                self.active_roi.active = False

            # disable the branch if the active roi is not a segment or a segment of another branch
            if self.active_segment is not None:
                if not hasattr(p,"parent") or p.parent is not self.active_segment.parent:
                    self.active_segment.parent.active = False

            # set new active roi
            self._activeroi = p

            # enable new active roi
            if p is not None:
                self.active_roi.active = True

                # enable/disable hold buttons
                for btn, axes in self.holdbuttons:
                    btn.setEnabled(p is not None)
                    checked = (p is not None) and (axes in p.holdaxes)
                    btn.setChecked(checked)

                # enable branch if active roi is a segment
                if self.active_segment is not None:
                    self.active_segment.parent.active = True

        self.fig.canvas.draw()


    @active_frame.setter
    def active_frame(self,f):
        with self.disable_draw():
            if not 0 <= f < self.data.shape[2]:
                raise Exception("Frame needs to be in range [0,{}]".format(self.data.shape[2]))

            self.__active_frame = f
            self.frameimg.set_data(self.data[...,f])

            # remove the markers
            if hasattr(self, "_DendriteSegmentationTool__active_frame_lines"):
                for l in self.__active_frame_lines:
                    l.remove()

            # redraw the markers
            self.__active_frame_lines = []
            for ax in self.timeaxes:
                l = ax.axvline(x = f, color = 'black', lw = 1.)
                self.__active_frame_lines.append(l)

        self.fig.canvas.draw()

    def toggle_overlay(self):
        self.show_overlay = not self.show_overlay

    def split_branches(self,length = None):
        with self.disable_draw():
            for b in self.branches:
                self.split_branch(b,length)
        self.fig.canvas.draw()

    def split_branch(self,branch = None, length = None):
        """
            Split one of the root branches into segments.
            Arguments: branch (defaults to active branch)
                       length (defaults to length from picker widget)
            Returns: nothing
        """
        branch = self.active_branch if branch is None else branch
        length = self.split_length  if length is None else length

        if branch is not None and branch in self.branches:
            branch.split(length = length)
        if branch.active:
            self.active_roi = branch.children[0]

    def split_segment(self,segment = None, parts = 2):
        """Split the given segment in to equal parts."""
        segment = self.active_segment if segment is None else segment

        # there might be no active segment
        if segment is None:
            return

        # get the index of the old segment in the parents child list
        i = segment.parent.children.index(segment)

        segment.split(nsegments = parts)
        if segment.parent.active:
            self.active_roi = segment.parent.children[i]

    def join_segments(self, segment = None, next = True):
        """
        Join two segments into one. Arguments:
            segment: A segment of any branch. Defaults to the active segment.
            next:    True or False, denote whether to join the segment with the preceeding or succeeding one.
        """
        segment = self.active_segment if segment is None else segment

        # there might be no active segment
        if segment is None:
            return

        # create and retrieve the new segment
        joined = segment.join(next = next)

        # make the new segment active
        if segment.parent.active:
            self.active_roi = joined

    @contextmanager
    def disable_draw(self):
        # store the original draw method
        draw = self.fig.canvas.draw

        def noop(*args):
            pass
            #print args
            #print "draw noop"

        # override the draw method as noop
        self.fig.canvas.draw = noop

        # yield and run code in context
        #print "<draw noop context"
        yield
        #print "<end draw noop context"

        # restore the original behaviour of draw
        self.fig.canvas.draw = draw


    def add_branch(self,branch):
        """
        Add a new branch to the list of managed branches.
        Args:
            branch: The branch to add. Expected to be of type swc.Branch.
        """
        branchroi = BranchRoi(branch = branch, datasource = self, axes = self)
        self.branches.append(branchroi)
        self.branchmask_creator.enabled = False
        self.btn_toggle_branchmask.setChecked(False)
        self.fig.canvas.draw()


    def __init__(self, data, swc, mean = None, pmin = 10, pmax = 99):
        """
        Create and show the gui for data analysis.
        Args:
            data:  The 3D dataset
            swc:   SWC File that allows looping over branches.
            mean: Background image. Defaults to data.mean(axis = -1)
            pmin,pmax: Percentiles for color range. I.e. the color range for mean and data will start at pmin %
                           and reach up to pmax %. Defaults to (10,99)
        """
        self.data = data
        self.swc = swc
        self.meandata = numpy.mean(data,axis = -1) if mean is None else mean

        self.fig = plt.figure()

        self.gs = gridspec.GridSpec(2, 1, height_ratios = [.3,.7])
        self.axraster = plt.subplot(self.gs[0])
        self.gsl = gridspec.GridSpecFromSubplotSpec(4, 2, subplot_spec=self.gs[1], height_ratios = [.6,1,1,1], hspace = 0.075)
        self.aximage  = plt.subplot(self.gsl[:,1])
        self.axtraceactive  = plt.subplot(self.gsl[0,0],sharex = self.axraster)
        self.axhold1 = plt.subplot(self.gsl[1,0],sharex = self.axraster)
        self.axhold2 = plt.subplot(self.gsl[2,0],sharex = self.axraster)
        self.axhold3 = plt.subplot(self.gsl[3,0],sharex = self.axraster)

        self.axtracehold = [self.axhold1,self.axhold2,self.axhold3]
        """ a list with the axes where traces can put on hold"""
        self.timeaxes = [self.axtraceactive] + self.axtracehold + [self.axraster]
        """ a list with all axes that have time as x axis"""

        # disable labels in the hold axes two timeaxes and label the active axes
        self.axtraceactive.tick_params(axis = 'x', labelbottom = False, labeltop = True)

        for ax in self.axtracehold:
            ax.tick_params(axis = 'x', labelbottom = False)

        for ax in self.timeaxes:
            ax.set_xlim(0,data.shape[-1])

        dx = data.shape[1]*0.26666
        dy = data.shape[0]*0.26666
        vmin,vmax = numpy.percentile(self.meandata.flatten(), q = [pmin,pmax])
        self.meanimg  = self.aximage.imshow(self.meandata,cmap = matplotlib.cm.gray,
                                        interpolation='nearest',vmin = vmin,vmax = vmax)

        red_alpha_cm = matplotlib.cm.get_cmap('jet')
        red_alpha_cm._init()
        red_alpha_cm._lut[:,-1] = numpy.linspace(.0, 1.0, red_alpha_cm.N+3)
        #red_alpha_cm.set_under([0,0,0,0])

        #norm = matplotlib.colors.LogNorm(.001,1.)
        x,y,t = self.data.shape
        vmin,vmax = numpy.nanpercentile(self.data[...,:min(t/10,50)], q = [pmin,pmax])
        norm = matplotlib.colors.Normalize(vmin = vmin, vmax = vmax, clip = True)
        self.frameimg = self.aximage.imshow(self.data[...,0],cmap = red_alpha_cm,norm = norm ,
                                        interpolation='nearest')
        # disable autoscale on image axes, to avoid rescaling due to additional artists.
        self.aximage.set_autoscale_on(False)

        self.fig.colorbar(self.frameimg,ax = self.aximage)
        self.threshold    = numpy.percentile(self.meandata.flatten(), q = 90)
        self.active_frame = 0

        self.colors = ['#CC0099','#CC3300','#99CC00','#00FF00','#006600','#999966']
        self.colorcycle = itertools.cycle(self.colors)

        # get all parts from the swc file that have at least one segment
        branches = [BranchRoi(branch = b, datasource = self, axes = self) for b in swc.branches if len(b) > 1]
        self.branches = bicyclelist(branches)
        """ The list which stores the branches loaded from swc. This list should not be modified"""

        self.polyrois = bicyclelist()
        """ The list which stores the polymask rois. Use app.add_polymask(roi) and app.remove_polymask(roi) to modify list."""

        self.pixelrois = bicyclelist()
        """ The list which stores the pixel mask rois. Use app.add_pixelmask(roi) and app.remove_pixelmask(roi) to modify list."""

        self.fig.canvas.set_window_title('DendriteSegmentationTool')
        #self.fig.canvas.mpl_disconnect(self.fig.canvas.manager.key_press_handler_id)
        self.fig.canvas.mpl_connect('pick_event', noraise(self.onpick))
        self.fig.canvas.mpl_connect('key_press_event', noraise(self.onkey))
        self.fig.canvas.mpl_connect('button_press_event',noraise(self.onclick))

        def add_action(name,func,tooltip, **kwargs):
            action = self.fig.canvas.manager.toolbar.addAction(name)
            action.setToolTip(tooltip)
            # use dumb.noraise to wrap the function in a try/except block
            # that will catch everything and print it to stdout
            # also filter away all args and kwargs which might come from the signal invocation
            action.triggered.connect(noraise(lambda *args, **kwargs: func()))
            for key,value in kwargs.iteritems():
                action.setProperty(key,value)
            return action

        self.fig.canvas.manager.toolbar.addSeparator()

        # ============ BRANCH AND SEGMENT NAVIGATION =================
        self.branchmask_creator = BranchMaskCreator(axes = self.aximage, canvas = self.fig.canvas,
                                                     update = self.fig.canvas.draw,
                                                     notify = self.add_branch)
        def enable_branch_mask_creator():
            self.branchmask_creator.enabled = True
        add_action("<<",self.previous_branch,"Select previous branch.")
        tooltip = "Create a new branch.\n Click for adding new segments, use '+'/'-' keys to adjust segment thicknes.\n Use 'z' key to undo last segment."
        self.btn_toggle_branchmask = add_action("+", enable_branch_mask_creator, tooltip, checkable = True)
        add_action(">>",self.next_branch,"Select next branch.")
        add_action("<",self.next_segment,"Select previous segment.")
        add_action(">",self.previous_segment,"Select next segment.")
        self.fig.canvas.manager.toolbar.addSeparator()

        # ============ BRANCH SPLITTING              =================
        add_action("split\nbranch", self.split_branch, "Split selected branch.")
        add_action("split\nall",self.split_branches,"Split all branches.")
        self.split_length_widget = QtGui.QSpinBox(value = 10)
        self.split_length_widget.setToolTip("Choose the spliting length.")
        self.fig.canvas.manager.toolbar.addWidget(self.split_length_widget)
        self.fig.canvas.manager.toolbar.addSeparator()

        # ============ SEGMENT MERGE AND SPLIT       =================
        #self.fig.canvas.manager.toolbar.addWidget(QtGui.QLabel("Segment:"))
        add_action("1/2", self.split_segment, "Split selected segment in two equal parts.")
        add_action("<+",lambda : self.join_segments(next = False), "Merge selected segment with preceeding segment.")
        add_action("+>",lambda : self.join_segments(next = True), "Merge selected segment with next segment.")
        self.fig.canvas.manager.toolbar.addSeparator()

        # ============ MASK AND THRESHOLD            =================
        self.btn_toggle_mask = add_action("Mask", self.toggle_overlay, "Toggle the mask overlay.",
                                         checkable = True, checked = True)
        def incr(): self.threshold = self.threshold*1.05
        def decr(): self.threshold = self.threshold/1.05
        add_action("-", decr, "Decrease masking threshold.")
        add_action("+", incr, "Increase masking thresold.")
        self.fig.canvas.manager.toolbar.addSeparator()

        # ============== FREEHAND SELECTION ===================
        tooltip = "Create a freehand polygon mask.\n" + \
                        "If the freehand mode is active each click into the 2D image\n" + \
                        "will add a corner to the polygon. Pressing <enter> will finish\n" + \
                        "(and close) the polygon."

        self.polymask_creator = PolyMaskCreator(axes = self.aximage,
                                  canvas = self.fig.canvas,
                                  update = self.fig.canvas.draw,
                                  notify = self.add_polyroi)
        self.btn_toggle_polymask = add_action("Poly", self.toggle_polymask_mode, tooltip, checkable = True)
        add_action("<", self.previous_polyroi, "Select the previous freehand polygon mask.")
        add_action(">", self.next_polyroi, "Select the next polygon mask.")
        add_action("del", self.remove_polyroi, "Remove the currently active polygon mask.")
        self.fig.canvas.manager.toolbar.addSeparator()

        # ============== PIXEL ROI SELECTION ===================
        tooltip = "Create freehand pixel masks.\n" + \
                        "If the freehand mode is active each click into the 2D image\n" + \
                        "will add a pixel to the pixel mask. Pressing <enter> will finish\n" + \
                        "the mask and the next clicks will create another pixel mask."

        self.pixelmask_creator = PixelMaskCreator(axes = self.aximage,
                                  canvas = self.fig.canvas,
                                  update = self.fig.canvas.draw,
                                  notify = self.add_pixelroi)
        self.btn_toggle_pixelmask = add_action("Pixel", self.toggle_pixelmask_mode, tooltip, checkable = True)
        add_action("<", self.previous_pixelroi, "Select the previous pixelmask.")
        add_action(">", self.next_pixelroi, "Select the next pixelmask")
        add_action("del", self.remove_pixelroi, "Remove the currently active pixelmask.")
        self.fig.canvas.manager.toolbar.addSeparator()

        # ============ TRACE PLOT CONTROL ====================
        def hold(ax):
            def func():
                print self.active_roi
                if self.active_roi is not None:
                    self.active_roi.toggle_hold(ax)
                self.fig.canvas.draw()
            return func
        #self.fig.canvas.manager.toolbar.addWidget(QtGui.QLabel("Hold traces:"))
        tooltip =  "Keep the trace of the currently selected segment in one of the hold axes."
        self.hold1 = add_action("H1", hold(self.axhold1),tooltip, checkable = True, enabled = False)
        self.hold2 = add_action("H2", hold(self.axhold2),tooltip, checkable = True, enabled = False)
        self.hold3 = add_action("H3", hold(self.axhold3),tooltip, checkable = True, enabled = False)
        self.holdbuttons = [(self.hold1, self.axhold1),(self.hold2,self.axhold2),(self.hold3,self.axhold3)]
        self.fig.canvas.manager.toolbar.addSeparator()

        # ================= Post Trace hooks ===================
        def postapply(cls,trace):
            import numpy
            import scipy
            if self.btn_toggle_detrend.isChecked():
                if not numpy.isinf(trace).any() and not numpy.isnan(trace).any():
                    trace = scipy.signal.detrend(trace)
            if self.btn_toggle_smoothen.isChecked():
                N = self.spin_smoothen.value()
                trace = numpy.convolve(trace, numpy.ones(shape = N), mode = 'same') / N
            return trace
        Roi.postapply = classmethod(postapply)

        self.btn_toggle_detrend  = add_action('Detrend',self.toggle_filter ,"Apply linear detrend on all traces bevore plotting.",  checkable = True)
        self.btn_toggle_smoothen = add_action('Smoothen',self.toggle_filter ,"Apply moving average filter with N frames on all traces bevore plotting. Select N with spin box to the right.",  checkable = True)
        self.spin_smoothen = QtGui.QSpinBox(value = 3)
        def refresh(arg):
            if self.btn_toggle_smoothen.isChecked():
                self.toggle_filter()
        self.spin_smoothen.setMinimum(2)
        self.spin_smoothen.setToolTip("Choose the number of frames for the moving average.")
        self.spin_smoothen.valueChanged.connect(refresh)
        self.fig.canvas.manager.toolbar.addWidget(self.spin_smoothen)

        # finally, select first branch
        self.next_branch()

    def toggle_filter(self):
        with self.disable_draw():
            Roi.tracecache.clear()
        self.fig.canvas.draw()

    def toggle_polymask_mode(self):
        self.polymask_creator.enabled = not self.polymask_creator.enabled

    def add_polyroi(self,x,y):
        polyroi = PolygonRoi(outline = numpy.array([x,y]).T,
                             axes = self, datasource = self)
        self.polyrois.append(polyroi)
        self.active_roi = self.polyrois[-1]
        self.polymask_creator.enabled = False
        self.btn_toggle_polymask.setChecked(False)

    def toggle_pixelmask_mode(self):
        self.pixelmask_creator.enabled = not self.pixelmask_creator.enabled

    def add_pixelroi(self,x,y):
        pixelroi = PixelRoi(pixels = [x,y],
                             axes = self, datasource = self)
        self.pixelrois.append(pixelroi)
        self.active_roi = self.pixelrois[-1]
        self.pixelmask_creator.enabled = False
        self.btn_toggle_pixelmask.setChecked(False)

    def remove_pixelroi(self,p = None):
        """remove given or active roi (if p is None) and make the next roi active."""
        if p is None:
            p = self.active_pixelroi
        if p is None:
            return
        p.remove()
        self.pixelrois.remove(p)
        self.active_roi = self.pixelrois.cur()

    def remove_polyroi(self,p = None):
        if p is None:
            p = self.active_polyroi
        if p is None:
            return
        p.remove()
        self.polyrois.remove(p)
        self.active_roi = self.polyrois.cur()

    def onkey(self,event):
        if event.inaxes in self.timeaxes and event.key == ' ':
            self.active_frame = int(event.xdata)
        if event.key == '+' and not self.branchmask_creator.enabled:
            self.threshold = self.threshold*1.05
        if event.key == '-' and not self.branchmask_creator.enabled:
            self.threshold = self.threshold/1.05
        if event.key  == 'm':
            self.toggle_overlay()

    def onclick(self,event):
        if event.inaxes is self.axraster:
            if self.active_branch is not None:
                index = int(event.ydata)
                if index < len(self.active_branch.children):
                    self.active_roi = self.active_branch.children[index]


    def onpick(self,event):
        if event.mouseevent.inaxes is self.aximage:
            if event.artist.roi is self.active_roi:
                # ignore the selection event for the active item
                # TODO: this doesnt work properyl, since the segment gets activated bevore the freehand onpick is evaluated
                # hence in the freehand onpick evaluation we reactivate the freehand even if it was the active selection
                # bevore onpick invocation
                return
            if event.artist.roi in self.polyrois:
                #print "fount polyroi, ignoring"
                return
                #self.active_poly = event.artist.roi
            for b in self.branches:
                if event.artist.roi in b.children:
                    #print "fount segmentroi"
                    self.active_roi = event.artist.roi
        elif event.mouseevent.inaxes in [self.axtraceactive] + self.axtracehold:
            #print "onpick for trace", event.artist
            # get the roi from the selected line
            if hasattr(event.artist,"roi"):
                roi = event.artist.roi
                # check whether the roi is a segment or freehand
                if roi in self.polyrois:
                    # its a freehand, make it active
                    self.active_roi = roi
                else:
                    # seach for segment in all branche's children
                    for b in self.branches:
                        if roi in b.children:
                            # found it, make it active
                            self.active_roi = roi
                # nothing found, ignore it

