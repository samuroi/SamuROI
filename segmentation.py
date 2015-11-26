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


class DendriteSegmentationTool(object):

    def calc_overlay(self,threshold = 140.):
        self.overlay_threshold = threshold
        #from skimage.filters import sobel
        elevation_map = skimage.filters.sobel(self.meandata)

        markers = numpy.zeros_like(self.meandata)
        markers[self.meandata < self.overlay_threshold] = 1
        markers[self.meandata > self.overlay_threshold*1.1] = 2
        segmentation = skimage.morphology.watershed(elevation_map, markers)

        overlay = numpy.zeros(shape = self.meandata.shape + (4,),dtype = float)
        overlay[...,3]= segmentation == 1
        self.mask, self.overlay = segmentation == 2, overlay

    def show_overlay(self):
        if not hasattr(self,"overlayimg"):
            self.overlayimg = self.axc.imshow(self.overlay,interpolation = 'nearest')

    def hide_overlay(self):
        if hasattr(self,"overlayimg"):
            self.overlayimg.remove()
            del self.overlayimg

    def toggle_overlay(self):
        if hasattr(self,"overlayimg"):
            self.hide_overlay()
        else:
            self.show_overlay()


    def __init__(self, data, swc, mean = None):
        self.data = data #scipy.signal.detrend(data)
        self.swc = swc
        self.meandata = numpy.mean(data,axis = -1) if mean is None else mean

        self.fig = plt.figure()

        gs = gridspec.GridSpec(5, 2,
                       width_ratios=[1,2],
                               height_ratios = [1,1,1,1,1]
                       )
        #self.axrasterspines = plt.subplot(gs[0,:])
        self.axraster = plt.subplot(gs[0,:])
        self.axc = plt.subplot(gs[1:,1])
        ax1 = plt.subplot(gs[1,0])
        ax2 = plt.subplot(gs[2,0],sharex=ax1,sharey=ax1)
        ax3 = plt.subplot(gs[3,0],sharex=ax1,sharey=ax1)
        ax4 = plt.subplot(gs[4,0],sharex=ax1,sharey=ax1)
        self.axeslist  =[ax1,ax2,ax3,ax4]
        for ax in self.axeslist:
            ax.set_autoscale_on(False)
            ax.set_ylim(-0.01,.01)
            ax.set_xlim(0,data.shape[-1])

        dx = data.shape[1]*0.26666
        dy = data.shape[0]*0.26666
        self.meanimg  = self.axc.imshow(self.meandata,cmap = matplotlib.cm.gray,
                                        interpolation='nearest',vmin = 100,vmax = 300)

        red_alpha_cm = matplotlib.cm.get_cmap('Reds')
        red_alpha_cm._init()
        red_alpha_cm._lut[:,-1] = numpy.linspace(.0, 1.0, red_alpha_cm.N+3)
        #red_alpha_cm.set_under([0,0,0,0])

        #norm = matplotlib.colors.LogNorm(.001,1.)
        norm = matplotlib.colors.Normalize(vmin = -.1,vmax = .5, clip = True)
        self.frameimg = self.axc.imshow(self.data[...,0],cmap = red_alpha_cm,norm = norm ,
                                        interpolation='nearest')

        self.fig.colorbar(self.frameimg,ax = self.axc)
        self.calc_overlay()
        self.show_overlay()

        self.thick = 5
        self.thin  = 1

        colors = ['#CC0099','#CC3300','#99CC00','#00FF00','#006600','#999966']
        self.colorcycle = itertools.cycle(colors)

        self.axescycle = itertools.cycle(self.axeslist)

        # store traces and detections for each segment
        self.traces   = {}
        self.detections   = {}
        self.segments = []
        self.spines   = []
        for branch in swc.branches:
            if len(branch)>1:
                tube = Polygon(branch.tube,fill = False, color = 'blue',picker = False,lw = self.thin)
                tube.branch = branch
                #self.axc.add_patch(tube)
            else:
                circle = Circle((branch['x'],branch['y']),branch['radius'],
                                facecolor = (0.1,0,0,.5), picker = False,
                                lw = self.thin,fill = False,
                                edgecolor = self.colorcycle.next())
                #collection = PatchCollection(cirles,)
                self.axc.add_patch(circle)
                circle.center = (branch['x'],branch['y'])
                circle.radius = branch['radius']
                circle.spans   = []
                circle.onaxes  = None
                circle.dependentartist = []
                self.spines.append(circle)
            for segment in branch.segments:
                color = self.colorcycle.next()
                patch = Polygon(segment,fill = False, picker = True,edgecolor=color,lw = self.thin)
                patch.parent  = tube
                patch.segment = segment
                patch.spans   = []
                patch.onaxes  = None
                patch.dependentartist = []
                self.axc.add_patch(patch)
                self.segments.append(patch)

        self.axraster.set_xlim([0,self.data.shape[-1]])
        self.fig.canvas.set_window_title('DendriteSegmentationTool')
        self.fig.canvas.mpl_disconnect(self.fig.canvas.manager.key_press_handler_id)
        self.fig.canvas.mpl_connect('pick_event', self.onpick)
        self.fig.canvas.mpl_connect('key_press_event', self.onkey)

    def update_segments(self):
        self.traces = {}
        self.detections = {}
        self.fig.canvas.set_window_title('Busy...')
        for i, patch in enumerate(self.segments):
            trace = patch.segment.trace(self.data,self.mask)
            mean = trace.mean()
            mean = 1 if mean == 0. else mean
            #self.traces[patch]     = (trace - self.F) / self.F
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
