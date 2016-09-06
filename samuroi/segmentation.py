import numpy
import skimage

import skimage.filters
import skimage.morphology

from cached_property import cached_property
from .maskset import MaskSet
from .util.event import Event


class Segmentation(object):
    def __init__(self, data):
        self.masks = MaskSet()
        """ A joined set of all rois. Allows for easy cycling through all rois. use app.rois.remove(roi) and app.rois.add(roi). To keep this set in a consistent state with the other sets."""

        self.data_changed = Event()
        self.overlay_changed = Event()
        self.postprocessor_changed = Event()

        self.postprocessor = self.no_postprocessor

        # call the property setter which will initialize the mean data and threshold value
        self.data = data

        # todo: the active frame is merely a utility to synchronize widgets. maybe it should go to the gui...
        self.active_frame_changed = Event()
        self.active_frame = 0

    @property
    def active_frame(self):
        return self.__active_frame

    @active_frame.setter
    def active_frame(self, f):
        if not 0 <= f < self.data.shape[2]:
            raise Exception("Frame needs to be in range [0,{}[".format(self.data.shape[2]))
        self.__active_frame = int(f)
        self.active_frame_changed()

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
        # clear meandata cache
        if hasattr(self, "meandata"):
            del self.meandata

        # choose some appropriate new threshold value
        self.threshold = numpy.percentile(self.meandata.flatten(), q=90)
        self.data_changed()

    @cached_property
    def meandata(self):
        return numpy.mean(self.data, axis=-1)

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

    def save_hdf5(self, filename, mask=True, pixels=True, branches=True, circles=True, polygons=True, data=False,
                  traces=True):
        """
        Create a hdf5 file holding the overlay mask, the rois and the traces of the current setup.
        The structure of the hdf5 file will be as follows:
            - mask (dataset, optional, binary mask defined by threshold value, threshold is stored as attribute)
            - data (dataset, optional, the full 3D dataset from which the traces were generated)
            - branches/circles... (groups holding different kinds of datasets for masks)
            - traces (group that holds a hierachy for the traces.)
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
            for m in self.pixelmasks:
                m.to_hdf5(f)

        if polygons:
            for m in self.polymasks:
                m.to_hdf5(f)

        if circles:
            for m in self.circlemasks:
                m.to_hdf5(f)

        if branches:
            for m in self.branchmasks:
                m.to_hdf5(f)

        if traces:
            f.create_group('traces')
            for m in self.masks:
                trace = self.postprocessor(m(self.data, self.overlay))
                if hasattr(m, "children"):
                    if 'traces/' + m.name not in f:
                        f.create_group('traces/' + m.name)
                    f.create_dataset('traces/' + m.name + '/trace', data=trace)
                else:
                    f.create_dataset('traces/' + m.name, data=trace)
            for m in self.branchmasks:
                if len(m.children) > 0:
                    f.create_dataset('traces/' + m.name + '/linescan', data=m.linescan(self.data, self.overlay))
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

    def load_hdf5(self, filename, mask=True, pixels=True, branches=True, circles=True, polygons=True, data=True):
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
                if (self.overlay != f['overlay']).any():
                    print "Warning: overlay threshold does not match with stored binary mask!"
                self.overlay = f['overlay'].value

            if data:
                if 'data' not in f:
                    raise Exception("Data not stored in given hd5 file.")
                self.data = f['data'].value

            if pixels:
                for m in PixelMask.from_hdf5(f):
                    self.masks.add(m)

            if polygons:
                for m in PolygonMask.from_hdf5(f):
                    self.masks.add(m)

            if circles:
                for m in CircleMask.from_hdf5(f):
                    self.masks.add(m)

            if branches:
                for m in BranchMask.from_hdf5(f):
                    self.masks.add(m)
