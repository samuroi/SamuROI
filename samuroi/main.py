import numpy

from samuroi import SamuROIWindow
from samuroi.plugins.tif import load_tif
from samuroi.plugins.swc import load_swc

import sys
from PyQt4 import QtGui

data = load_tif('/home/enigma/charite/testmartin/ fast time single channel72.tif')
swc = load_swc('/home/enigma/charite/testmartin/ fast time single channel72.swc')

segmentation = numpy.zeros(shape=(data.shape[0:2]), dtype=int)
segmentation[100:140,100:150] = 1
segmentation[130:140,130:150] = 3

segmentation[30:80,30:80] = 6
segmentation[40:70,40:70] = 40

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    # show the gui for the filtered data
    mainwindow = SamuROIWindow(data=data)

    mainwindow.segmentation.load_swc(swc)
    from samuroi.masks.segmentation import Segmentation as SegmentationMask
    mainwindow.segmentation.masks.add(SegmentationMask(data = segmentation,name = "test"))
    mainwindow.show()
    sys.exit(app.exec_())
