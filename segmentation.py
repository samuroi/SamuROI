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

from .maskset import MaskSet
# from .artists.roi import Roi
# from .artists.pixelroi import PixelRoi
# from .artists.polyroi import PolygonRoi
# from .artists.branchroi import BranchRoi
# from .artists.circleroi import CircleRoi

from .util.event import Event


# TODO change roi bicyclelist to builtin set type
# TODO give rois an id property which can be used as hashable for the set
# TODO create treeview widget for roi list overview
# TODO status bar which denotes the roi which is active (number and type)
# TODO untangle roi data/view functionality

class Segmentation(object):
    def __init__(self, data, mean=None):
        self.masks = MaskSet()
        """ A joined set of all rois. Allows for easy cycling through all rois. use app.rois.remove(roi) and app.rois.add(roi). To keep this set in a consistent state with the other sets."""

        self.data_changed = Event()
        self.overlay_changed = Event()
        self.postprocessor_changed = Event()

        self.postprocessor = self.no_postprocessor
        self.data = data
        self.meandata = numpy.mean(data, axis=-1) if mean is None else mean
        self.threshold = numpy.percentile(self.meandata.flatten(), q=90)

    @property
    def pixelmasks(self):
        from .masks.pixel import PixelMask
        if PixelMask not in self.masks.types():
            return
        for i in self.masks[PixelMask]:
            yield i

    @property
    def branchmasks(self):
        from .masks.branch import BranchMask
        if BranchMask not in self.masks.types():
            return
        for i in self.masks[BranchMask]:
            yield i

    @property
    def circlemasks(self):
        from .masks.circle import CircleMask
        if CircleMask not in self.masks.types():
            return
        for i in self.masks[CircleMask]:
            yield i

    @property
    def polymasks(self):
        from .masks.polygon import PolygonMask
        if PolygonMask not in self.masks.types():
            return
        for i in self.masks[PolygonMask]:
            yield i

    def split_branches(self, length):
        for b in self.branchmasks:
            b.split(length=length)

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, d):
        self.__data = d
        self.data_changed()

    @property
    def overlay(self):
        return self.__overlay

    @overlay.setter
    def overlay(self, m):
        if m.shape != self.data.shape[0:2]:
            raise Exception("Mask and data shape need to match.")
        if m.dtype != bool:
            raise Exception("Mask dtype needs to be boolean")

        self.__overlay = m
        self.overlay_changed()

    @property
    def threshold(self):
        return self.__threshold

    @threshold.setter
    def threshold(self, t):
        self.__threshold = t
        elevation_map = skimage.filters.sobel(self.meandata)

        markers = numpy.zeros_like(self.meandata)
        markers[self.meandata < self.threshold] = 1
        markers[self.meandata > self.threshold * 1.1] = 2
        segmentation = skimage.morphology.watershed(elevation_map, markers)

        self.overlay = segmentation == 2

    @property
    def no_postprocessor(self):
        def identity(x):
            return x

        return identity

    @property
    def postprocessor(self):
        """A function that postprocesses traces"""
        return self.__postprocessor

    @postprocessor.setter
    def postprocessor(self, pp):
        self.__postprocessor = pp
        self.postprocessor_changed()

    def save_hdf5(self, filename, mask=True, pixels=True, branches=True, circles=True, freehands=True, data=False,
                  traces=True):
        """
        Create a hdf5 file holding the overlay mask, the rois and the traces of the current setup.
        The structure of the hdf5 file will be as follows:
            - mask (dataset, optional, binary mask defined by threshold value, threshold is stored as attribute)
            - data (dataset, optional, the full 3D dataset from which the traces were generated)
            - branches (group holding subgroups for each branch)
                - 0 (group for an individual branch)
                    - roi (dataset, definition of the branch, (x,y,z,r) tuples)
                    - trace (dataset, trace of branch)
                    - linescan (dataset. combined traces of all children of the branch, only present if branch is segmented)
                    - outline (dataset, Nx2)
                    - segments (group holding segment subgroups)
                        - 0 (group for an individual segment)
                            - roi (dataset, definition of the segment, (x,y,z,r) tuples)
                            - trace (dataset, trace of segment)
                            - outline (dataset. Nx2)
                        - ... (more segments)
                - ... (more branches)
            - circles (group holding subgroups for each circle roi)
                - 0 (group for individual roi)
                    - roi (dataset, (x,y,r))
                    - trace (dataset)
                - ... (more circles)
            - freehands
                - 0 (group for individual roi)
                    - roi (dataset, the outline of the polygon, Nx2)
                    - trace (dataset)
                - ... (more polygons)
            - pixels
                - 0 (group for individual roi)
                    - roi (dataset, the pixel coordinates, shape: 2xN)
                    - trace (dataset)
                - ... (more pixels)
        Args:
            filename: filename to use, suffix ".h5" will be added if missing.
            mask: flag whether mask should be stored in file. default = True
            data: flag whether data should be stored in file. default = False
        """
        import h5py
        f = h5py.File(filename, mode='w')
        f.clear()
        if mask:
            f.create_dataset('overlay', data=self.overlay)
            f['overlay'].attrs['threshold'] = self.threshold
        if data:
            f.create_dataset('data', data=self.data)

        if pixels:
            f.create_group('pixels')
            for i, m in enumerate(self.pixelmasks):
                f.create_dataset('pixels/' + str(i) + '/roi', data=m.pixels)
                if traces:
                    f.create_dataset('pixels/' + str(i) + '/trace', data=m(self.data, self.overlay))

        if freehands:
            f.create_group('freehands')
            for i, m in enumerate(self.polymasks):
                f.create_dataset('freehands/' + str(i) + '/roi', data=m.outline)
                if traces:
                    f.create_dataset('freehands/' + str(i) + '/trace', data=m(self.data, self.overlay))

        if circles:
            f.create_group('circles')
            for i, m in enumerate(self.circlemasks):
                data = [m.center[0], m.center[1], m.radius]
                f.create_dataset('circles/' + str(i) + '/roi', data=data)
                if traces:
                    f.create_dataset('circles/' + str(i) + '/trace', data=m(self.data, self.overlay))

        if branches:
            for i, b in enumerate(self.branchmasks):
                f.create_group('branches/{}'.format(i))
                # f.create_dataset('branches/{}/roi'.format(i), data=b.branch)
                f.create_dataset('branches/{}/outline'.format(i), data=b.outline)
                if traces:
                    f.create_dataset('branches/{}/trace'.format(i), data=b(self.data, self.overlay))
                if len(b.children) > 0:
                    f.create_dataset('branches/{}/linescan'.format(i), data=b.linescan(self.data,self.overlay))
                f.create_group('branches/{}/segments'.format(i))
                for j, s in enumerate(b.children):
                    f.create_group('branches/{}/segments/{}'.format(i, j))
                    # f.create_dataset('branches/{}/segments/{}/roi'.format(i, j), data=s.branch)
                    f.create_dataset('branches/{}/segments/{}/outline'.format(i, j), data=s.outline)
                    if traces:
                        f.create_dataset('branches/{}/segments/{}/trace'.format(i, j), data=s(self.data, self.overlay))
        # write stuff to disc
        f.close()

    def load_swc(self, swc):
        # get all parts from the swc file that have at least one segment
        from .masks.circle import CircleMask
        from .masks.branch import BranchMask
        for b in swc.branches:
            if len(b) > 1:
                mask = BranchMask(data=b)
            else:
                mask = CircleMask(center=b[['x', 'y']][0], radius=b['radius'][0])
            self.masks.add(mask)

    def load_hdf5(self, filename, mask=True, pixels=True, branches=True, circles=True, freehands=True, data=True):
        """

        Args:
            filename:
            mask:
            branches:
            circles:

        Returns:

        """
        from .masks.pixel import PixelMask
        from .masks.branch import BranchMask
        from .masks.circle import CircleMask
        from .masks.polygon import PolygonMask

        import h5py
        with h5py.File(filename, mode='r') as f:
            if mask:
                if 'overlay' not in f:
                    raise Exception("Overlay data not stored in given hd5 file.")
                self.threshold = f['overlay'].attrs['threshold']
                if (self.mask != f['overlay']).any():
                    print "Warning: overlay threshold does not match with stored binary mask!"
                self.mask = f['overlay'].value

            if data:
                if 'data' not in f:
                    raise Exception("Data not stored in given hd5 file.")
                self.data = f['data'].value

            if pixels:
                if 'pixels' not in f:
                    raise Exception("pixels not stored in given hd5 file.")
                for i, p in f['pixels'].items():
                    self.masks.add(PixelMask(p['roi'].value))

            if freehands:
                if 'freehands' not in f:
                    raise Exception("freehands not stored in given hd5 file.")
                for i, p in f['freehands'].items():
                    self.masks.add(PolygonMask(p['roi'].value))

            if circles:
                if 'circles' not in f:
                    raise Exception("circles not stored in given hd5 file.")
                for i, p in f['circles'].items():
                    center = p['roi'].value[0:2]
                    radius = p['roi'].value[2]
                    self.masks.add(CircleMask(center=center, radius=radius))

            if branches:
                from dumb.util.swc import Branch
                if 'branches' not in f:
                    raise Exception("branches not stored in given hd5 file.")
                for i, p in f['branches'].items():
                    d = p['roi'].value
                    self.masks.add(BranchMask(x=d['x'], y=d['y'], z=d['z'], r=d['radius']))
