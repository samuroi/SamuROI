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

###  TODO liste
# - unselect everything
# - taste für nächstes/vorheriges (OP) segment anzeigen, start from the last selected (if ctrl go to next/previous where any event was detected)
# - W neues fenter für neue trace
# - J neue trace in gleichem fenster
# - A average over the selected traces (start average in new window)
# - moving average filter für traces (variable fenstergröße)
# - click on detected event (d) delete event from list
# - 4 axes -> 1 axes
# - freehand seletion
###
#import branch
##class Branch(branch.Branch):
#def __init__


class DendriteSegmentationTool(object):


    threshold      = property(_get_threshold, _set_threshold)
    show_overlay   = property(_get_show_overlay,_set_show_overlay)
    active_branch  = property(_get_active_branch, _set_active_branch)
    active_segment = property(_get_active_segment, _set_active_segment)
    split_length   = property(_get_split_length, _set_split_length)

    def _get_split_length(self):
        return self.split_length_widget.value()

    def _set_split_length(self,v):
        self.split_length_widget.setValue(v)

    def _get_threshold(self):
        return self.__threshold

    def _set_threshold(self,t):
        self.__threshold = t
        #from skimage.filters import sobel
        elevation_map = skimage.filters.sobel(self.meandata)

        markers = numpy.zeros_like(self.meandata)
        markers[self.meandata < self.threshold] = 1
        markers[self.meandata > self.threshold*1.1] = 2
        segmentation = skimage.morphology.watershed(elevation_map, markers)

        overlay = numpy.zeros(shape = self.meandata.shape + (4,),dtype = float)
        overlay[...,3] = segmentation == 1
        if not hasattr(self,overlayimg):
            self.overlayimg = self.aximage.imshow(overlay,interpolation = "nearest")
        else:
            self.overlayimg.set_data(overlay)
        self.overlayimg
        self.mask = segmentation == 2
        self.fig.canvas.draw()

    def _get_show_overlay(self):
        return self.overlayimg.get_visible()

    def _set_show_overlay(self, v):
        self.overlayimg.set_visible(v)
        self.mask_checkbox.setChecked(v)


    def next_branch(self):
        if len(self.branches) > 0:
            self.active_branch = self.branch_cycle.next()

    def previous_branch(self):
        if len(self.branches) > 0:
            self.active_branch = self.branch_cycle.prev()

    def next_segment(self):
        if self.active_branch is not None:
            if hasattr(self.active_branch,"children"):
                if len(self.active_branch.children)>0:
                    self.active_segment = self.active_branch.children_cycle.next()

    def previous_segment(self):
        if self.active_branch is not None:
            if hasattr(self.active_branch,"children"):
                if len(self.active_branch.children)>0:
                    self.active_segment = self.active_branch.children_cycle.prev()

    def _get_active_branch(self):
        if hasattr(self,"_DendriteSegmentationTool__active_branch"):
            return self.__active_branch
        return None

    def _set_active_branch(self,b):
        # hide artists of previous branch
        if self.active_branch is not None:
            self.active_branch.artist.set_linewidth(self.thin)
            self.axtracebranch.lines[0].remove()

        self.__active_branch = b
        if b is not None:
            b.artist.set_linewidth(self.thick)
            b.trace = b.polymask(data,self.mask)
            self.axtracebranch.plot(b.trace)
            if hasattr(b,"children"):
                self.next_segment()
            else:
                self.fig.canvas.draw()

    def _get_active_segment(self):
        if hasattr(self,"_DendriteSegmentationTool__active_segment"):
            return self.__active_segment
        return None

    def _set_active_segment(self,s):
        # hide artists of previous branch
        if self.active_segment is not None:
            self.active_segment.artist.set_linewidth(self.thin)
            self.axtracesegment.lines[0].remove()

        self.__active_segment = s
        if s is not None:
            s.artist.set_linewidth(self.thick)
            s.trace = s.polymask(data,self.mask)
            self.axtracesegment.plot(s.trace)
        self.fig.canvas.draw()


    def toggle_overlay(self):
        self.show_overlay = not show_overlay

    def split_branches(self,length = None):
        for b in self.branches:
            self.split_branch(b,length,nsemgnets)

    def split_branch(self,branch = None, length = None):
        """
            Split one of the root branches into segments.
            Arguments: branch (defaults to active branch)
                       length (defaults to length from picker widget)
            Returns: nothing
        """
        branch = self.active_branch if branch is None else branch
        length = self.split_length  if length is None else length
        if branch is None:
            return
        assert(branch in self.branches)

        # if the branch has childrens, remove them
        if hasattr(branch, "children"):
            for child in branch.children:
                child.artist.remove()

        # split branch and reset childrens
        branch.children = branch.split(length = length)
        branch.children_cycle = bicycle(branch.children)

        # draw artists for childrens
        colorcycle = itertools.cycle(self.colors)
        for child in branch.children:
            child.artist   = Polygon(child.outline, fill = False, color = colorcycle.next(),picker = False,lw = self.thin)
            child.parent   = branch
            child.polymask = PolyMask(child.outline)
            self.aximage.add_patch(child.artist)

        self.active_branch = branch

    def split_segment(self,segment,parts = 2):
        """Split the given segment in to equal parts."""
        segment = self.active_segment if segment is None else segment

        # there might be no active segment
        if segment is None:
            return

        # remove the old polygon artist
        segment.artist.remove()

        # get the index of the old segment in the parents child list
        i = segment.parent.children.index(segment)

        # split and replace the old segment by the two new ones
        segment.parent.children[i:i+1] = subsegments = segment.split(nsegments = 2)
        for ss in subsegments:
            ss.artist   = Polygon(ss.outline, fill = False, color = self.colorcycle.next(),picker = False,lw = self.thin)
            ss.parent   = segment.parent
            ss.polymask = PolyMask(ss.outline)

        self.active_segment = subsegments[0]

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

        # the list of childrens of the parent
        childrens = segment.parent.children

        # get the index of the segment in the parents child list
        i = childrens.index(segment)

        # select the slice of the two segments to join
        # this will work event for i = 0,1,len(childrens)-1 and len(childrens)
        s = slice(i,i+2) if next else slice(i-1,i+1)

        # we cant join next/previous, if there is no respective other segment
        if len(childrens[s])<2:
            return

        # remove the old artists
        for child in children[s]:
            child.artist.remove()

        # create joined segment and replace the two old ones in list
        childrens[s] = joined = childrens[s][0].append(childrens[s][1])

        # setup the new segment
        joined.artist   = Polygon(joined.outline, fill = False, color = self.colorcycle.next(),picker = False,lw = self.thin)
        joined.parent   = segment.parent
        joined.polymask = PolyMask(joined.outline)

        self.active_segment = joined


    def __init__(self, data, swc, mean = None):
        self.data = data
        self.swc = swc
        self.meandata = numpy.mean(data,axis = -1) if mean is None else mean

        self.fig = plt.figure()

        gs = gridspec.GridSpec(2, 1, height_ratios = [.3,.7])
        self.axraster = plt.subplot(gs[0)
        gsl = gridspec.GridSpecFromSubplotSpec(3, 2, subplot_spec=gs[1])
        self.aximage  = plt.subplot(gsl[:,1])
        self.axtracebranch  = plt.subplot(gsl[0,0])
        self.axtracesegment = plt.subplot(gsl[1,0])
        self.axtracemulti   = plt.subplot(gsl[2,0])

        for ax in [self.axraster,self.axtracebranch,self.axtracesegment,self.axtracemulti]:
            ax.set_xlim(0,data.shape[-1])

        dx = data.shape[1]*0.26666
        dy = data.shape[0]*0.26666
        self.meanimg  = self.axc.imshow(self.meandata,cmap = matplotlib.cm.gray,
                                        interpolation='nearest',vmin = 100,vmax = 300)

        red_alpha_cm = matplotlib.cm.get_cmap('jet')
        red_alpha_cm._init()
        red_alpha_cm._lut[:,-1] = numpy.linspace(.0, 1.0, red_alpha_cm.N+3)
        #red_alpha_cm.set_under([0,0,0,0])

        #norm = matplotlib.colors.LogNorm(.001,1.)
        norm = matplotlib.colors.Normalize(vmin = -.1,vmax = .5, clip = True)
        self.frameimg = self.axc.imshow(self.data[...,0],cmap = red_alpha_cm,norm = norm ,
                                        interpolation='nearest')

        self.fig.colorbar(self.frameimg,ax = self.axc)
        self.threshold = 140

        self.thick = 5
        self.thin  = 1

        self.colors = ['#CC0099','#CC3300','#99CC00','#00FF00','#006600','#999966']
        self.colorcycle = itertools.cycle(colors)

        # get all parts from the swc file that have at least one segment
        self.branches = [Branch(b) for b in swc.branches if len(b) > 1]
        self.branch_cycle = bicycle(self.branches)
        for branch in self.branches:
            branch.artist   = Polygon(branch.outline, fill = False, color = self.colorcycle.next(),picker = False,lw = self.thin)
            branch.polymask = PolyMask(branch.outline)
            self.aximage.add_patch(branch.artist)
        self.next_branch()

        self.fig.canvas.set_window_title('DendriteSegmentationTool')
        #self.fig.canvas.mpl_disconnect(self.fig.canvas.manager.key_press_handler_id)
        #self.fig.canvas.mpl_connect('pick_event', self.onpick)
        #self.fig.canvas.mpl_connect('key_press_event', self.onkey)

        def exception_proxy(func):
            try:
                func()
            except Exception as e:
                import sys, traceback
                traceback.print_exc(file=sys.stdout)
                print e

        def add_action(name,func,tooltip):
            action = self.fig.canvas.manager.toolbar.addAction(name)
            action.setToolTip(tooltip)
            action.connect(exception_proxy(func))

        self.fig.canvas.manager.toolbar.addSeparator()

        # ============ BRANCH AND SEGMENT NAVIGATION =================
        add_action("<<",self.next_branch,"Select next branch.")
        add_action(">>",self.previous_branch,"Select previous branch.")
        add_action("<",self.next_segment,"Select next segment.")
        add_action("<",self.previous_segment,"Select previous segment.")
        self.fig.canvas.manager.toolbar.addSeparator()

        # ============ BRANCH SPLITTING              =================
        self.fig.canvas.manager.toolbar.addWidget(PyQt4.QLabel("Split:"))
        add_action("branch", self.split_branch, "Split selected branch.")
        add_action("all",self.split_branches,"Split all branches.")
        self.split_length_widget = QtGui.QSpinBox(value = 10)
        self.fig.canvas.manager.toolbar.addWidget(self.split_length_widget)
        self.fig.canvas.manager.toolbar.addSeparator()

        # ============ SEGMENT MERGE AND SPLIT       =================
        self.fig.canvas.manager.toolbar.addWidget(PyQt4.QLabel("Segment:"))
        add_action("1/2", self.split_segment, "Split selected segment in two equal parts.")
        add_action("<+",lambda : self.join_segments(next = False), "Merge selected segment with preceeding segment.")
        add_action("+>",lambda : self.join_segments(next = True), "Merge selected segment with next segment.")
        self.fig.canvas.manager.toolbar.addSeparator()

        # ============ MASK AND THRESHOLD            =================
        self.fig.canvas.manager.toolbar.addWidget(PyQt4.QLabel("Mask:"))
        self.mask_checkbox = QtGui.QCheckBox(checked = True)
        self.fig.canvas.manager.toolbar.addWidget(self.mask_checkbox)
        def incr(): self.threshold = self.threshold*1.05
        def decr(): self.threshold = self.threshold/1.05
        add_action("-",lambda : decr, "Decrease masking threshold.")
        add_action("+",lambda : incr, "Increase masking thresold.")
        self.fig.canvas.manager.toolbar.addSeparator()

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
        """
        # THIS IS SHIT, since it allows overlap of spines with segments, still, i dont know how to cut off
        # where a segment begins
        for i, spine in enumerate(self.spines):
            print "spi",
            # since we artificially increased swc radii to have more pixels within a segments and the
            # boundary detected by scikit watershed, correct this increment here to reduce overlap with other
            # segments
            c,r = spine.center, spine.radius / 2.5
            rowslice = slice(max(0,c[1]-r),min(self.data.shape[0],c[1]+r))
            colslice = slice(max(0,c[0]-r),min(self.data.shape[1],c[0]+r))
            masked = self.data[rowslice,colslice,:]*self.mask[rowslice,colslice,numpy.newaxis]
            spine.trace = masked.mean(axis = 0).mean(axis = 0)
            spine.detection = find_events(spine.trace,
                                                 equal_var = False,
                                                 pvalue = 0.05,
                                                 taumin = 15)

            if spine.onaxes is not None:
                ax = spine.onaxes
                self.unselect_segment(spine)
                self.select_segment(spine, ax)
        """
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

        """
        for i, spine in enumerate(self.spines):
            # remove old raster plot
            if hasattr(spine, "rasterbars"):
                spine.rasterbars.remove()

            # create new raster plot
            detection = spine.detection
            color     = spine.get_edgecolor()
            xranges   = [[s,e-s] for s,e in zip(detection.starts,detection.ends)]
            if len(xranges) > 0:
                spine.rasterbars = self.axraster.broken_barh(xranges = xranges, yrange = (i/4.,1),
                                                             linewidth = spine.get_linewidth(),
                                                             alpha = 0.25, color = color,picker =True)
                spine.rasterbars.spine = spine
        """

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

    def toggle_segment(self,segment):
        if segment.get_linewidth() == self.thin:
            self.select_segment(segment)
        else:
            self.unselect_segment(segment)

    def onkey(self,event):
        #print event.key
        try:
            if event.inaxes in self.axeslist and event.key == ' ':
                t = int(event.xdata)
                self.frameimg.set_data(self.data[...,t])
                self.fig.canvas.draw()
            if event.key == '+':
                self.hide_overlay()
                self.calc_overlay(self.overlay_threshold*1.05)
                self.show_overlay()
                self.fig.canvas.draw()
            if event.key == '-':
                self.hide_overlay()
                self.calc_overlay(self.overlay_threshold*0.95)
                self.show_overlay()
                self.fig.canvas.draw()
            if event.key == 'enter':
                self.update_segments()
                self.redraw_raster()
                self.fig.canvas.draw()
            if event.key  == 'm':
                self.toggle_overlay()
                self.fig.canvas.draw()
            if event.key == 'u':
                pass
            if event.key == 's':
                return
        except Exception as e:
            import sys, traceback
            traceback.print_exc(file=sys.stdout)
            print e

    def splitsegment(self,artist):
        # create two sub polygons from given polygon artist
        if hasattr(artist,"children"):
            return
        artist.children = []
        segment = artist.segment
        for subsegment in segment.subsegments:
            color = self.colorcycle.next()
            childartist = Polygon(subsegment,fill = False, picker = True,edgecolor=color,lw = 1)
            childartist.parent = artist
            childartist.segment = subsegment
            artist.children.append(childartist)
            self.axc.add_patch(childartist)
        self.fig.canvas.draw()

    def onpick(self,event):
        try:
            if event.mouseevent.inaxes is self.axc:
                if event.artist in self.segments:
                    self.toggle_segment(event.artist)
            elif event.mouseevent.inaxes is self.axraster:
                self.toggle_segment(event.artist.segment)

        except Exception as e:
            import sys, traceback
            traceback.print_exc(file=sys.stdout)
            print e
