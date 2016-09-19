import sys
from PyQt4 import QtGui

# only necessary from within scripts
app = QtGui.QApplication(sys.argv)

# samuroi imports
from samuroi import SamuROIWindow
from samuroi.plugins.tif import load_tif

# load the data into a 3D numpy array
data = load_tif('/path/to/your/file.tif')

# show the gui for the loaded data
mainwindow = SamuROIWindow(data=data)

# maybe necessary depending on IPython
mainwindow.show()

# get handle on the document of the main window
doc = mainwindow.segmentation

def add_some_segmentation():


# only necessary in scripts
sys.exit(app.exec_())
