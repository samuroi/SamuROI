How ROIs work in SamuROI
------------------------
.. note:: In the following we will use mask as synonym for ROI.

SamuROI comes with a set of predefined types of ROIs. Those are:

- pixel based ROI (:py:class:`samuroi.masks.pixel.PixelMask`):
   This roi holds a list of pixels for which the trace is calculated as average over all those pixels.
- circle shaped ROI (:py:class:`samuroi.masks.circle.CircleMask`):
   This roi is defined by a center and radius. The resulting trace takes all pixels into account that intersect
   with the circle.
- branch ROI (:py:class:`samuroi.masks.branch.BranchMask`):
   This roi is intended for one dimensional structures within the video data.
   It provides functionality to be split into child sub segments. Child masks can be accessed with
   :py:attr:`samuroi.masks.branch.BranchMask.children`.
- polygon ROI (:py:class:`samuroi.masks.polygon.PolygonMask`):
   As the name states, this class represents arbitrary polygon shapes.
- segmentations (:py:class:`samuroi.masks.segmentation.Segmentation`):
   This class is rather special, since it is not a real ROI, but a set of rois defined by a 2D array with the same
   shape as the video resolution.

All of these classes inherit from a common base class :py:class:`samuroi.masks.mask.Mask` which requires the derived
classes to implement an "apply" function :py:meth:`samuroi.masks.mask.Mask.__call__`. Whenever a trace of a roi is
calculated this function will be called on the respective roi object.

The :py:class:`samuroi.masks.branch.BranchMask` and the :py:class:`samuroi.masks.segmentation.Segmentation` also have a
set of child masks.

For examples how to work with these classes see :ref:`working-with-rois`.
