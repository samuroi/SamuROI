import numpy

from samuroi.gui.samuroiwindow import SamuROIWindow
from samuroi.plugins.tif import load_tif
from samuroi.plugins.swc import load_swc
from samuroi.masks.segmentation import Segmentation as SegmentationMask

import sys
from PyQt4 import QtGui

import argparse

parser = argparse.ArgumentParser(description='Open SamuROI and load some data.')

parser.add_argument('filename', type=str, help='The filename of the tif file to use as data.')

parser.add_argument('--swc', dest='swcfiles', type=str, action='append', help='Filename of swc file to load.')

parser.add_argument('--segmentation', dest='segmentations', type=str, action='append',
                    help='Filename of segmentations to load. (.npy files)')

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    args = parser.parse_args()

    data = load_tif(args.filename)
    morphology = numpy.max(data, axis=-1)

    from samuroi.plugins.baseline import linbleeched_deltaF

    data = linbleeched_deltaF(data)

    # show the gui for the filtered data
    mainwindow = SamuROIWindow(data=data, morphology = morphology)

    for filename in args.swcfiles:
        swc = load_swc(filename)
        mainwindow.segmentation.load_swc(swc)

    if args.segmentations is not None:
        for filename in args.segmentations:
            segdata = numpy.load(filename)
            seg = SegmentationMask(data=segdata, name="filename")
            mainwindow.segmentation.masks.add(seg)

    mainwindow.show()
    sys.exit(app.exec_())
