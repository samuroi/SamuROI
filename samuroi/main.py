import polf
import numpy

from polf import Recording

from dumb.util import SWCFile
from dumb.util import baseline, deltaF, power_spectrum, bandstop

import scipy.signal
import matplotlib.pyplot as plt

from epo import DendriteSegmentationTool
import glob

import sys
from PyQt4 import QtGui


def scale_swc(swc):
    swc.radius = swc.radius * 3
    return swc


polf.Recording.path = property(lambda self: self.datafile.dirname())
polf.Recording.swcfile = property(lambda self: scale_swc(SWCFile(glob.glob(self.path + "/*.swc")[0])))
polf.Recording.stabilized = property(lambda self: numpy.load(glob.glob(self.path + "/*.npy")[0]))

prefix = '/home/enigma/charite/testmartin/ fast time single channel72'
rec = Recording(prefix=prefix)

data = rec.data()

segmentation = numpy.zeros(shape=(data.shape[0:2]), dtype=int)
segmentation[100:140,100:150] = 1
segmentation[130:140,130:150] = 3

segmentation[30:80,30:80] = 6
segmentation[40:70,40:70] = 40

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    # show the gui for the filtered data
    mainwindow = DendriteSegmentationTool(data=data, mean=data[..., 0])

    mainwindow.segmentation.load_swc(rec.swcfile)
    from epo.masks.segmentation import Segmentation as SegmentationMask
    mainwindow.segmentation.masks.add(SegmentationMask(data = segmentation,name = "test"))
    mainwindow.show()
    sys.exit(app.exec_())
