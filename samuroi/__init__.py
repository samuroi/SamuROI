# check if a QtApplication is already running, otherwise create one here
# todo: maybe this should go to the guis __init__ file...
from PyQt4 import QtGui

if QtGui.QApplication.instance() is None:
    import sys
    QtGui.QApplication(sys.argv)

from .gui.samuroiwindow import SamuROIWindow
from .samuroidata import SamuROIData
