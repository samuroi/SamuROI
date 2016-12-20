Examples
========

This section presents some example code snippets which are ment to be run from within a Jupyter notebook.
All examples can be found in the git repository in ``doc/examples``.
If you want to run SamuROI from within scripts, see :ref:`script-example`.

Lets get started with how to show the GUI window.
Only a few lines are required to load a tif file and show up the gui:

.. literalinclude:: examples/gui.py
   :lines: 7-18

The underlying SamuROIData object
---------------------------------

SamuROI tries to follow a strict separation of data and GUI which is sometimes referred as Document/View or Model/View
pattern (for more infos see the technical description in the paper and the documentation of
:py:class:`samuroi.SamuROIData`).
When a SamuROI window is created, it also creates an underlying SamuROIData object which can be obtained by:

.. code-block:: python

   # get handle on the document of the main window
   doc = mainwindow.segmentation

In the following examples we will show how one can read and manipulate many of the attributes of the
:py:class:`samuroi.SamuROIData` class.


.. _working-with-rois:

Working with ROIs
^^^^^^^^^^^^^^^^^

All ROIs of a SamuROIData object are stored within the attribute masks of type :py:class:`samuroi.maskset.MaskSet`.
This class keeps track of the types of masks it stores and provides events for added and removed masks. It is iterable
and checks that no mask is added twice (one can add multiple copies of a mask, but not the same object).
Iteration over all masks is simple as

.. code-block:: python

   # iterate over all masks
   for m in doc.masks:
      print m

Because the :py:class:`samuroi.maskset.MaskSet` also introduces a hierarchy for the types of masks it stores, one can
also iterate through all masks of a certain type like this:

.. code-block:: python

   # iterate over all branch masks
   from samuroi.masks.branchmask import BranchMask
   for bm in doc.masks[BranchMask]:
      print bm

Since masks are stored in a set, the cannot be retrieved by a specific index, i.e. the following wont work:

.. code-block:: python

   # iterate over all branch masks
   first_mask = doc.masks[0] # ERROR, cannot use [0] to get first of an iterable
   first_branch = doc.masks[BranchMask][0] # ERROR, same as above

Instead masks can be identified by their name:

.. warning:: There can be multiple masks with the same name. It is up to the user to ensure that the name is unique.

.. code-block:: python

   # iterate over all branch masks
   from samuroi.masks.branchmask import BranchMask
   for bm in doc.masks[BranchMask]:
      if bm.name == 'my_special_branch':
         break

   print bm.name # yeah, I found my mask

Alternatively:

.. code-block:: python

   mybranch = next(branch for branch in doc.masks[BranchMask] if branch.name == 'my_special_branch')


Extracting a trace from a mask
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In SamuROI, the masks itself are distinct objects which do not know about data and overlay. Hence calculate the trace of
for a mask, one has to combine the 3D dataset, the 2D overlay mask and the geometric information from the mask itself.
Because the geometric information is different for different kind of masks (e.g. Circle, Polygon, or Segmentation) this
combination is done by the mask itself (:py:meth:`samuroi.mask.Mask.__call__`):

.. code-block:: python

   # get some mask
   mybranch = next(doc.masks[BranchMask])

   # combine data, overlay and geometry
   trace = mybranch(doc.data,doc.overlay)

   # thats it, trace now is a 1D numpy array, we can e.g. plot it with matplotlib
   plt.figure()
   plt.plot(trace)


Internally, the SamuROI widgets do the very same thing to plot their data.


Extracting detected events
^^^^^^^^^^^^^^^^^^^^^^^^^^
Running the event detection will add detection results to all mask. Having a detection result does not mean, that there is an
event. The detection result only describes the outcome of the event detection. For the implemented event detection based on
template matching (`Clements, J.M. Bekkers <http://dx.doi.org/10.1016/S0006-3495(97)78062-7>`_) this result hold the optimal scaling and offset values,
aswell as the "matching criterion" curve. This data can be accessed via:

.. code-block:: python

   # get some mask
   mybranch = next(doc.masks[BranchMask])

   # print the detection results
   print mybranch.events # This only works, if one has done an event detection run before!

   # maybe plot the matching criterion ?
   plt.figure()
   plt.plot(mybranch.events.crit)


Adding and removing masks
^^^^^^^^^^^^^^^^^^^^^^^^^

We can simply add and remove rois from the :py:class:`samuroi.maskset.MaskSet`. E.g. we can add all masks from a swc
file like this. (If you need this functionality you can also call :py:meth:`samuroi.SamuROIData.load_swc`)

.. code-block:: python

  from samuroi.masks.circle import CircleMask
  from samuroi.masks.branch import BranchMask
  from samuroi.plugins.swc import load_swc
  swc = load_swc("path/to/file.swc")
  for b in swc.branches:
      if len(b) > 1:
          mask = BranchMask(data=b)
      else:
          mask = CircleMask(center=b[['x', 'y']][0], radius=b['radius'][0])
      # this will add the mask to the maskset and trigger maskset's added event.
      doc.masks.add(mask)

Removing masks is similar

.. code-block:: python

  from samuroi.masks.branch import BranchMask
  # use try catch since there might not be any BranchMask in the MaskSet
  try:
      # get handle on the "first" branch in the maskset
      first_branch = doc.masks[BranchMask].next()
      # remove the mask, will trigger the preremove and removed event of the masklist.
      doc.masks.discard(first_branch)
  except:
      # we cant remove anything if its not there
      pass

.. warning:: Removing masks from the maskset from within an iteration through
               its elements may lead to undefined behaviour.

Installing a custom postprocessor
---------------------------------
Often one wants to apply some custom postprocessor to traces produces by the ROIs. This can be achieved by installing a
custom postprocessor. E.g. if you click on the "detrend" and "smoothen" buttons in the gui, respective postprocessors
will transform the trace before it gets displayed in any widget. In this example we will show how we can transform the
trace such that it has a zero mean over time.

.. code-block:: python

  def zero_mean_postprocessor(trace):
    """
    :param trace: a 1D numpy array holding the trace of the ROI.
    :return: a 1D numpy array with transformed trace.
    """
    return trace - numpy.mean(trace)

  # change the postprocessor
  doc.postprocessor = zero_mean_postprocessor

Pretty easy, huh? For something more advanced, an event detection postprocessor and best fit overlay, have a look at :ref:`script-example`!

.. _script-example:

SamuROI from within normal python scripts
-----------------------------------------
Usually the IPython notebook takes care of some Qt mechanics that are required by SamuROI.
Specifically this is: The Qt main event loop, which handles all direct user input on the GUI.
Hence when one wants to run SamuROI from within a script, this handling has to be done by one self.
The following example shows what is necessary and provides a nice starting point for your own applications :-)

.. literalinclude:: examples/script.py