from PyQt4 import QtGui


class ViewMenu(QtGui.QMenu):
    def __init__(self, parent):
        super(ViewMenu, self).__init__(parent)

        self.toggle_treeview = QtGui.QAction('Tree &view', self)
        self.toggle_treeview.setCheckable(True)
        self.toggle_treeview.setChecked(self.parent().roitreedockwidget.isVisible())
        self.toggle_treeview.triggered.connect(lambda b: self.parent().roitreedockwidget.setVisible(b))

        self.toggle_linescan = QtGui.QAction('&Linescan', self)
        self.toggle_linescan.setCheckable(True)
        self.toggle_linescan.setChecked(self.parent().linescandockwidget.isVisible())
        self.toggle_linescan.triggered.connect(lambda b: self.parent().linescandockwidget.setVisible(b))

        self.toggle_trace = QtGui.QAction('&Trace', self)
        self.toggle_trace.setCheckable(True)
        self.toggle_trace.setChecked(self.parent().tracedockwidget.isVisible())
        self.toggle_trace.triggered.connect(lambda b: self.parent().tracedockwidget.setVisible(b))

        self.setTitle("&View")
        self.setToolTip("Show/Hide the docked tool frames.")

        self.addAction(self.toggle_treeview)
        self.addAction(self.toggle_linescan)
        self.addAction(self.toggle_trace)
