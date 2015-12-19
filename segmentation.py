import numpy
import scipy
import skimage
import matplotlib
import itertools

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from matplotlib.patches import Circle, Polygon
from matplotlib.collections import PatchCollection, PolyCollection

import skimage.filters
import skimage.morphology

from dumb.util import find_events
from dumb.util import baseline
from dumb.util import deltaF
from dumb.util import bicycle
from dumb.util import PolyMask
from dumb.util import noraise

from .branch import Branch
from .polyroi import PolygonRoi
from .branchroi import BranchRoi

from PyQt4 import QtGui

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
        self.__threshold = t
        elevation_map = skimage.filters.sobel(self.meandata)

        markers = numpy.zeros_like(self.meandata)
        markers[self.meandata < self.threshold] = 1
        markers[self.meandata > self.threshold*1.1] = 2
        segmentation = skimage.morphology.watershed(elevation_map, markers)

        overlay = numpy.zeros(shape = self.meandata.shape + (4,),dtype = float)
        overlay[...,3] = segmentation == 1
        if not hasattr(self,"overlayimg"):
            print "plotting overlay"
            self.overlayimg = self.aximage.imshow(overlay,interpolation = "nearest")
        else:
            self.overlayimg.set_data(overlay)
        self.mask = segmentation == 2
        # force recalculation of traces
        PolygonRoi.tracecache.clear()
        self.fig.canvas.draw()

    @property
    def show_overlay(self):
        return self.overlayimg.get_visible()

    @show_overlay.setter
    def show_overlay(self, v):
        # see if value changed
        b = self.show_overlay
        self.overlayimg.set_visible(v)
        self.mask_checkable.setChecked(v)
        if (b and not v) or (v and not b):
            self.fig.canvas.draw()

    def next_branch(self):
        if len(self.branches) > 0:
            self.active_branch = self.branch_cycle.next()

    def previous_branch(self):
        if len(self.branches) > 0:
            self.active_branch = self.branch_cycle.prev()

    def next_segment(self):
        if self.active_branch is not None:
            self.active_segment = self.active_branch.next_segment()
            self.fig.canvas.draw()

    def previous_segment(self):
        if self.active_branch is not None:
            self.active_segment = self.active_branch.previous_segment()
            self.fig.canvas.draw()

    @property
    def active_branch(self):
        for b in self.branches:
            if b.active:
                return b
        return None

    @active_branch.setter
    def active_branch(self,b):
        if self.active_branch is b:
            return
        # hide artists of previous branch
        if self.active_branch is not None:
            self.active_branch.active = False

        if b is not None:
            assert(b in self.branches)
            b.active = True
        self.fig.canvas.draw()

    @property
    def active_segment(self):
        if self.active_branch is not None:
            return self.active_branch.active_segment
        return None

    @active_segment.setter
    def active_segment(self,s):
        if self.active_segment is s:
            return
        if self.active_segment is not None:
            self.active_segment.active = False
        if s is not None:
            if self.active_branch is not s.parent:
                self.active_branch = s.parent
            self.active_branch.active_segment = s

        # enable/disable hold buttons
        for btn, axes in self.holdbuttons:
            btn.setEnabled(s is not None)
            checked = (s is not None) and (axes in s.holdaxes)
            btn.setChecked(checked)

        self.fig.canvas.draw()

    @property
    def active_frame(self):
        return self.__active_frame

    @active_frame.setter
    def active_frame(self,f):
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
        for ax in [self.axtraceactive] + self.axtracehold:
            l = ax.axvline(x = f, color = 'black', lw = 1.)
            self.__active_frame_lines.append(l)

        self.fig.canvas.draw()

    def toggle_overlay(self):
        self.show_overlay = not self.show_overlay

    def split_branches(self,length = None):
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
            self.active_segment = branch.children[0]

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
            self.active_segment = segment.parent.children[i]

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
            self.active_segment = joined

    def __init__(self, data, swc, mean = None, pmin = 10, pmax = 99):
        """
            Parameters:
                data:  The 3D dataset
                swc:   SWC File that allows looping over branches.
                mean:  Background image. Defaults to data.mean(axis = -1)
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
        self.axtraceactive  = plt.subplot(self.gsl[0,0])
        self.axhold1 = plt.subplot(self.gsl[1,0])
        self.axhold2 = plt.subplot(self.gsl[2,0])
        self.axhold3 = plt.subplot(self.gsl[3,0])

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
        vmin,vmax = numpy.nanpercentile(self.data, q = [pmin,pmax])
        norm = matplotlib.colors.Normalize(vmin = vmin, vmax = vmax, clip = True)
        self.frameimg = self.aximage.imshow(self.data[...,0],cmap = red_alpha_cm,norm = norm ,
                                        interpolation='nearest')

        self.fig.colorbar(self.frameimg,ax = self.aximage)
        self.threshold    = 140
        self.active_frame = 0

        self.colors = ['#CC0099','#CC3300','#99CC00','#00FF00','#006600','#999966']
        self.colorcycle = itertools.cycle(self.colors)

        # get all parts from the swc file that have at least one segment
        self.branches = [BranchRoi(branch = b, datasource = self, axes = self) for b in swc.branches if len(b) > 1]
        self.branch_cycle = bicycle(self.branches)

        # select first
        self.next_branch()

        self.fig.canvas.set_window_title('DendriteSegmentationTool')
        #self.fig.canvas.mpl_disconnect(self.fig.canvas.manager.key_press_handler_id)
        #self.fig.canvas.mpl_connect('pick_event', self.onpick)
        self.fig.canvas.mpl_connect('key_press_event', self.onkey)

        def add_action(name,func,tooltip, **kwargs):
            action = self.fig.canvas.manager.toolbar.addAction(name)
            action.setToolTip(tooltip)
            # use dumb.noraise to wrap the function in a try/except block
            # that will catch everything and print it to stdout
            action.triggered.connect(noraise(func))
            for key,value in kwargs.iteritems():
                action.setProperty(key,value)
            return action

        self.fig.canvas.manager.toolbar.addSeparator()

        # ============ BRANCH AND SEGMENT NAVIGATION =================
        add_action("<<",self.previous_branch,"Select previous branch.")
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
        self.fig.canvas.manager.toolbar.addWidget(QtGui.QLabel("Segment:"))
        add_action("1/2", self.split_segment, "Split selected segment in two equal parts.")
        add_action("<+",lambda : self.join_segments(next = False), "Merge selected segment with preceeding segment.")
        add_action("+>",lambda : self.join_segments(next = True), "Merge selected segment with next segment.")
        self.fig.canvas.manager.toolbar.addSeparator()

        # ============ MASK AND THRESHOLD            =================
        self.mask_checkable = add_action("Mask", self.toggle_overlay, "Toggle the mask overlay.", checkable = True)
        def incr(): self.threshold = self.threshold*1.05
        def decr(): self.threshold = self.threshold/1.05
        add_action("-", decr, "Decrease masking threshold.")
        add_action("+", incr, "Increase masking thresold.")
        self.fig.canvas.manager.toolbar.addSeparator()

        # ============ TRACE PLOT CONTROL ====================
        def hold(ax):
            def func():
                if self.active_segment is not None:
                    self.active_segment.toggle_hold(ax)
                self.fig.canvas.draw()
            return func
        self.fig.canvas.manager.toolbar.addWidget(QtGui.QLabel("Hold traces:"))
        tooltip =  "Keep the trace of the currently selected segment in one of the hold axes."
        self.hold1 = add_action("H1", hold(self.axhold1),tooltip, checkable = True, enabled = False)
        self.hold2 = add_action("H2", hold(self.axhold2),tooltip, checkable = True, enabled = False)
        self.hold3 = add_action("H3", hold(self.axhold3),tooltip, checkable = True, enabled = False)
        self.holdbuttons = [(self.hold1, self.axhold1),(self.hold2,self.axhold2),(self.hold3,self.axhold3)]
        self.fig.canvas.manager.toolbar.addSeparator()

        # ============== FREEHAND SELECTION ===================
        self.freehand_mode = False
        tooltip = """Change to freehand selection mask creation mode.
                     next line
                     foobar
                  """
        self.freehand_creator = PolyRoiCreator(axes = self.aximage,
                                  canvas = self.fig.canvas,
                                  update = self.fig.canvas.draw,
                                  notify = self.add_freehand_poly, enabled = False )
        self.freehand = add_action("FreeHand", self.toggle_freehand_mode, tooltip, checkable = True)


    @property
    def active_poly(self):
        if not hasattr(self,"polyrois"):
            return None
        for p in self.polyrois:
            if p.active:
                return p
        return None

    @active_poly.setter
    def active_poly(self,p):
        if self.active_poly

    def toggle_freehand_mode(self):
        self.freehand_creator.enabled = not self.freehand_creator.enabled

    def add_freehand_poly(self,x,y):
        if not hasattr(self, "polyrois"):
            self.polyrois = []
        polyroi = PolygonRoi(outline = numpy.array([x,y]).T,
                             axes = self, datasource = self)
        self.polyrois.append()

    def update_segments(self):
        self.traces = {}
        self.detections = {}
        self.fig.canvas.set_window_title('Busy...')
        for i, patch in enumerate(self.segments):
            trace = patch.segment.trace(self.data,self.mask)
            mean = trace.mean()
            mean = 1 if mean == 0. else mean
            #self.traces[patch]     = (trace - self.F) / self.F
            if numpy.isnan(trace).any() or numpy.isinf(trace).any():
                trace = numpy.zeros_like(trace)
            self.traces[patch]     = scipy.signal.detrend(trace)#trace#scipy.signal.detrend((trace - mean)/mean)
            self.detections[patch] = find_events(self.traces[patch],
                                                 equal_var = False,
                                                 pvalue = 0.05,
                                                 taumin = 15)
            if patch.onaxes is not None:
                ax = patch.onaxes
                self.unselect_segment(patch)
                self.select_segment(patch, ax)

            self.fig.canvas.set_window_title(self.fig.canvas.get_window_title() + '.')

        self.fig.canvas.set_window_title('DendriteSegmentationTool')

    def redraw_raster(self):
        nsegments = len(self.segments)
        nspines   = len(self.spines)
        for i, patch in enumerate(self.segments):
            # remove old raster plot
            if hasattr(patch, "rasterbars"):
                patch.rasterbars.remove()

            # create new raster plot
            detection = self.detections[patch]
            color     = patch.get_edgecolor()
            xranges   = [[s,e-s] for s,e in zip(detection.starts,detection.ends)]
            if len(xranges) > 0:
                patch.rasterbars = self.axraster.broken_barh(xranges = xranges, yrange = (i/4.,1),
                                                             linewidth = patch.get_linewidth(),
                                                             alpha = 0.25, color = color,picker =True)
                patch.rasterbars.segment = patch



    def select_segment(self,segment,targetax = None):
        # check if it is already selected
        if segment.get_linewidth() == self.thick:
            return

        targetax = self.axescycle.next() if targetax is None else targetax
        color = segment.get_edgecolor()[:-1]
        segment.set_linewidth(self.thick)
        for span in segment.spans:
            span.set_linewidth(self.thick)

        # if we did not yet calculate any segment information, we need to do it now
        if segment not in self.traces:
            self.update_segments()

        trace     = self.traces[segment]
        detection = self.detections[segment]

        # create a list or artists that should be removed when the artist is toggled off
        # plot returns that list already holding the one line
        segment.traceline, = targetax.plot(trace,color = color,lw = 0.5)
        xranges = [[s,e-s] for s,e in zip(detection.starts,detection.ends)]
        if len(xranges) > 0:
            segment.eventbars  = targetax.broken_barh(xranges = xranges,
                                                      yrange = (-1,2),alpha = 0.25,color = color)

        segment.onaxes = targetax
        if hasattr(segment,"rasterbars"):
            segment.rasterbars.set_linewidth(self.thick)

        segment.pscatter = targetax.scatter(detection.putative, detection.pvalues,color = 'black')

        segment.texts = []
        for ps,p,r in zip(detection.putative,detection.pvalues,detection.reason):
            te = targetax.text(x= ps, y = 0,s=str(r),color = 'black',
                               ha = 'center',va = 'center',size = 20,clip_on=True)
            segment.texts.append(te)
        mi,ma = targetax.get_ylim()
        mi = min(mi,numpy.min(trace)*1.1)
        ma = max(ma,numpy.max(trace)*1.1)
        targetax.set_ylim(mi,ma)
        self.fig.canvas.draw()

    def unselect_segment(self,segment):
        # check if it is already unselected
        if segment.get_linewidth() == self.thin:
            return
        segment.set_linewidth(self.thin)
        for span in segment.spans:
            span.set_linewidth(self.thin)
        if hasattr(segment,"traceline"):
            segment.traceline.remove()
            del segment.traceline
        if hasattr(segment,"eventbars"):
            segment.eventbars.remove()
            del segment.eventbars
        if hasattr(segment,"rasterbars"):
            segment.rasterbars.set_linewidth(self.thin)
        if hasattr(segment,"pscatter"):
            segment.pscatter.remove()
            del segment.pscatter
        if hasattr(segment,"texts"):
            for t in segment.texts:
                t.remove()
            del segment.texts

        segment.onaxes = None
        self.fig.canvas.draw()

    #def onclick()

    def onkey(self,event):
        try:
            if event.inaxes in self.timeaxes and event.key == ' ':
                self.active_frame = int(event.xdata)
            if event.key == '+':
                self.threshold = self.threshold*1.05
            if event.key == '-':
                self.threshold = self.threshold/1.05
            if event.key  == 'm':
                self.toggle_overlay()
        except Exception as e:
            import sys, traceback
            traceback.print_exc(file=sys.stdout)
            print e

    def onpick(self,event):
        try:
            if event.mouseevent.inaxes is self.aximage:
                if event.artist in self.segments:
                    self.toggle_segment(event.artist)
            elif event.mouseevent.inaxes is self.axraster:
                self.toggle_segment(event.artist.segment)

        except Exception as e:
            import sys, traceback
            traceback.print_exc(file=sys.stdout)
            print e
