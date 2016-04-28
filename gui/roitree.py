from PyQt4 import QtCore, QtGui

from PyQt4.QtCore import QVariant, QObject, pyqtSignal

from .roiitemmodel import RoiTreeModel


class RoiTreeWidget(QtGui.QTreeView):
    # proxy pyqt signals that can dispatch an out of thread event into the qt event loop
    mask_selected = pyqtSignal(object)
    mask_deselected = pyqtSignal(object)

    def __init__(self, parent, model, selectionmodel):
        QtGui.QTreeView.__init__(self, parent)

        # allow multi selection with shift and ctrl
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setModel(model)

        self.setSelectionModel(selectionmodel)#.selectionChanged.connect(self.on_selection_changed)

