import numpy
import skimage

import skimage.filters
import skimage.morphology

from cached_property import cached_property
from .maskset import MaskSet
from .util.event import Event


class SamuROIData(object):
    """
    This is the main data structure of SamuROI.
    It combines various aspects of rois, overlays and the video data that is to be analysed.

    The most important data attributes of this class are (see respective documentation for further info):

    - :py:attr:`samuroi.SamuROIData.masks`
    - :py:attr:`samuroi.SamuROIData.data`
    - :py:attr:`samuroi.SamuROIData.threshold`
    - :py:attr:`samuroi.SamuROIData.overlay`
    - :py:attr:`samuroi.SamuROIData.postprocessor`

    Whenever some of there attributes are changed via their property setter functions (e.g. `samudata.threshold = 5`)
    those setters will emit a signal via some event object (see :py:class:`samuroi.util.event.Event`).
    E.g. the events for the above attributes are:

    - :py:attr:`samuroi.maskset.MaskSet.added` and :py:attr:`samuroi.maskset.MaskSet.removed`
    - :py:attr:`samuroi.SamuROIData.data_changed`
    - :py:attr:`samuroi.SamuROIData.update_threshold`
    - :py:attr:`samuroi.SamuROIData.overlay_changed`
    - :py:attr:`samuroi.SamuROIData.postprocessor_changed`

    If one wants to get notified about any of those changes, one can simply connect to the events:

    .. code-block:: python

        def my_callback():
            print "I got triggered :-D"
        samudata.masks.added.append(my_callback)

    In this manner GUI updates and other custom tasks can be completely separated from the data structure.
    """

    def __init__(self, data, morphology=None):
        """
        This function will set up the underlying data structure. If no morphology is provided, the morphology array will
        be generated as `numpy.max(data,axis=-1)`, i.e. a maximum projection over data along the time axis.
        :param data:
        :param morphology: This can either be a 2D numpy array with the same shape as the video, or None.
        """
        self.postprocessor = self.no_postprocessor

        # call the property setter which will initialize the mean data and threshold value
        self.data = data

        if morphology is None:
            self.morphology = numpy.max(data, axis=-1)
        else:
            self.morphology = morphology

        # todo: the active frame is merely a utility to synchronize widgets. maybe it should go to the gui...
        self.active_frame = 0

    @cached_property
    def masks(self):
        """
        A joined set of all masks of type :py:class:`samuroi.maskset.MaskSet`.
        Use `masks.remove(some_mask)` and `masks.add(some_mask)` to manipulate the set.
        Insertions and removements will trigger events that can be connected to.
        """
        return MaskSet()

    @cached_property
    def data_changed(self):
        """This is a signal which should be triggered whenever the underlying 3D numpy data has changed."""
        return Event()

    @cached_property
    def overlay_changed(self):
        """This is a signal which should be triggered whenever the 2D overlay mask has changed."""
        return Event()

    @cached_property
    def postprocessor_changed(self):
        """This is a signal which should be triggered whenever the postprocessor has changed."""
        return Event()

    @cached_property
    def active_frame_changed(self):
        """This is a signal which should be triggered whenever the active frame has changed."""
        return Event()

    @cached_property
    def threshold_changed(self):
        """This signal will be triggered when the threshold is changed."""
        return Event()

    @cached_property
    def morphology_changed(self):
        """This signal will be triggered when the morphology image changed."""
        return Event()

    @property
    def active_frame(self):
        """
        The number of the selected frame of the dataset.

        :getter: Set active frame number.
        :setter: Change to some other frame. This will trigger the :py:attr:`samuroi.SamuROIData.active_frame_changed` event.
        :type: int in range `[0,n_frames(`
        """
        return self.__active_frame

    @active_frame.setter
    def active_frame(self, f):
        if not 0 <= f < self.data.shape[2]:
            raise Exception("Frame needs to be in range [0,{}[".format(self.data.shape[2]))
        self.__active_frame = int(f)
        self.active_frame_changed()

    @property
    def pixelmasks(self):
        """
        :return: A generator object that allows iteration over all pixel masks in the document.
        """
        from .masks.pixel import PixelMask
        if PixelMask not in self.masks.types():
            return
        for i in self.masks[PixelMask]:
            yield i

    @property
    def branchmasks(self):
        """
        :return: A generator object that allows iteration over all branch masks in the document.
        """
        from .masks.branch import BranchMask
        if BranchMask not in self.masks.types():
            return
        for i in self.masks[BranchMask]:
            yield i

    @property
    def circlemasks(self):
        """
        :return: A generator object that allows iteration over all circle masks in the document.
        """
        from .masks.circle import CircleMask
        if CircleMask not in self.masks.types():
            return
        for i in self.masks[CircleMask]:
            yield i

    @property
    def polymasks(self):
        """
        :return: A generator object that allows iteration over all polygon masks in the document.
        """
        from .masks.polygon import PolygonMask
        if PolygonMask not in self.masks.types():
            return
        for i in self.masks[PolygonMask]:
            yield i

    @property
    def segmentationmasks(self):
        """
        :return: A generator object that allows iteration over all segmentation masks in the document.
        """
        from .masks.segmentation import Segmentation
        if Segmentation not in self.masks.types():
            return
        for i in self.masks[Segmentation]:
            yield i

    @property
    def data(self):
        """
        The main video data onto which all masks get applied.

        :getter: Get the present video data.
        :setter: Change to some other video data. Changing the data will trigger the :py:attr:`samuroi.SamuROIData.data_changed` event.
        :type: 3d numpy array dtype should be float or int
        """
        return self.__data

    @data.setter
    def data(self, d):
        self.__data = d

        self.data_changed()

    @property
    def morphology(self):
        """
        An image which describes the static morphology. A good choice is to use the maximum projection over the non
        normalized data.
        :getter: obtain the morphology image.
        :setter: set the morphology image, will trigger the :py:attr:`samuroi.SamuROIData.morphology_changed` event.
        :type: 2D numpy array with same image shape as data.
        """
        return self.__morphology

    @morphology.setter
    def morphology(self, morphology):
        if (morphology.shape != self.data.shape[0:2]):
            raise Exception("Invalid morphology shape.")
        self.__morphology = morphology
        # choose some appropriate new threshold value
        self.threshold = numpy.percentile(self.morphology.flatten(), q=90)
        self.morphology_changed()

    @property
    def overlay(self):
        """
        The overlay is a binary mask with the same shape as the video data such that it can be applied to every frame
        of the video data. One can automatically set an overlay via :py:attr:`samuroi.SamuROIData.threshold`, or provide a custom overlay.

        :getter: Get the present overlay
        :setter: Set the overlay to given binary mask. This will trigger overlay_changed.
        :type: numpy.ndarray(dtype=bool,shape=self.data.shape[0:2])
        """
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
        """
        The threshold value controls the overlay mask.
        Higher threshold values will exclude larger areas.
        Lower threshold values are less restrictive. The threshold value will be initialized to the 90percentile of the
        mean data.

        :getter: Get the present threshold value
        :setter: Set the threshold value. This will trigger a recalculation of :py:attr:`samuroi.SamuROIData.overlay` which in
                    turn will trigger overlay_changed.
        :type: float
        """
        return self.__threshold

    @threshold.setter
    def threshold(self, t):
        self.__threshold = t
        self.threshold_changed()
        elevation_map = skimage.filters.sobel(self.morphology)

        markers = numpy.zeros_like(self.morphology)
        markers[self.morphology < self.threshold] = 1
        markers[self.morphology > self.threshold * 1.1] = 2
        segmentation = skimage.morphology.watershed(elevation_map, markers)

        self.overlay = segmentation == 2

    @property
    def no_postprocessor(self):
        """
        :return: A default postprocessor which does nothing.
        """

        def identity(x):
            return x

        return identity

    @property
    def postprocessor(self):
        """
        A postprocessor is a function which can be applied on traces.
        It takes a 1D numpy array as argument and returns a transformed array with the same shape.
        Defaults to :py:attr:`samuroi.SamuROIData.no_postprocessor`.

        :getter: get the function object.
        :setter: set the function object. Will trigger postprocessor_changed event.
        :type: callable object (1D numpy array -> 1D numpy array)
        """
        return self.__postprocessor

    @postprocessor.setter
    def postprocessor(self, pp):
        self.__postprocessor = pp
        self.postprocessor_changed()

    def save_hdf5(self, filename, mask=True, pixels=True, branches=True, circles=True, polygons=True, data=False,
                  traces=True, segmentations=True):
        """
        The structure of the hdf5 file will be as follows:

        - overlay (dataset, optional, binary mask defined by threshold value, threshold is stored as attribute)
        - data (dataset, optional, the full 3D dataset from which the traces were generated)
        - branches/circles... (groups holding different kinds of datasets for masks)
        - traces (group that holds a hierarchy for the traces.)

        :param filename: filename to use, suffix ".h5" will be added if missing.
        :param mask: flag whether mask should be stored in file.
        :param pixels:
        :param branches:
        :param circles:
        :param polygons:
        :param data: flag whether data should be stored in file.
        :param traces:
        :return:
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

        if segmentations:
            for m in self.segmentationmasks:
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
        """
        Load the content from the given swc object.

        Branches with only a single coordinate will be loaded as circles.
        Branches with more than one coordinate as "tubes".

        :param swc: A object of type :py:class:`samuroi.plugins.swc.SWCFile`.
        """
        # get all parts from the swc file that have at least one segment
        from .masks.circle import CircleMask
        from .masks.branch import BranchMask
        for b in swc.branches:
            if len(b) > 1:
                mask = BranchMask(data=b)
            else:
                mask = CircleMask(center=b[['x', 'y']][0], radius=b['radius'][0])
            self.masks.add(mask)

    def load_hdf5(self, filename, mask=True, pixels=True, branches=True, circles=True, polygons=True, data=True, segmentations=True):
        """
        Load data that from hd5 file.

        :param filename: The filename/path to read from (include extension)
        :param mask: flag whether to read the mask if it is stored in file.
        :param pixels: flag whether to read the pixel masks if some are stored in file.
        :param branches: flag whether to read the branch masks if some are stored in file.
        :param circles: flag whether to read the circle masks if some are stored in file.
        :param polygons: flag whether to read the polygon masks if some are stored in file.
        :param data: flag whether to read the data if it is stored in file.
        :param segmentations: flag whether to read the segmentations if it is stored in file.
        """
        from .masks.pixel import PixelMask
        from .masks.branch import BranchMask
        from .masks.circle import CircleMask
        from .masks.polygon import PolygonMask
        from .masks.segmentation import Segmentation

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

            if segmentations:
                for m in Segmentation.from_hdf5(f):
                    self.masks.add(m)
