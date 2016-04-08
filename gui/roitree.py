from PyQt4 import QtCore, QtGui

from PyQt4.QtCore import QVariant


class TreeItem(object):
    def child(self, row):
        raise NotImplementedError()

    def parent(self):
        raise NotImplementedError()

    def row(self, child):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()


class RootItem(TreeItem):
    def __init__(self, rois):
        # the list of lists holding the rois
        self.rois = rois

    # @property
    # def groups(self):
    #     return [RoiGroupItem(parent=self, rois=self.rois, type=t) for t in self.types]

    @property
    def types(self):
        return [t for t in set(type(roi) for roi in self.rois)]

    def row(self, child):
        assert (type(child) is RoiGroupItem)
        return self.types.index(child.type)

    def child(self, row):
        type = self.types[row]
        return RoiGroupItem(parent = self,rois = self.rois, type = type) #self.groups[row]

    def parent(self):
        return None

    def __len__(self):
        return len(set(type(roi) for roi in self.rois))


class RoiGroupItem(TreeItem):
    def __init__(self, parent, rois, type):
        self.rois = rois
        self.type = type
        self.__parent = parent

    @property
    def items(self):
        return [roi for roi in self.rois if type(roi) is self.type]

    def row(self, child):
        return self.items.index(child.item)

    def child(self, row):
        return RoiItem(parent = self,item = self.rois[row])

    def parent(self):
        return self.__parent

    def __len__(self):
        return 0#len(self.items)

    def __repr__(self):
        return "RoiGroup: " + str(self.type.__name__)


class RoiItem(TreeItem):
    def __init__(self, parent, item):
        self.item = item
        self.__parent = parent

    def row(self, child):
        return None

    def child(self, row):
        return None

    def __len__(self):
        return 0

    def parent(self):
        return self.__parent


class RoiTreeModel(QtCore.QAbstractItemModel):
    def __init__(self, rois, parent=None):
        super(RoiTreeModel, self).__init__(parent)
        self.root = RootItem(rois=rois)

    def flags(self, index):
        """Determines whether a field is editable, selectable checkable etc"""
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

    def columnCount(self, parent):
        """Returns the number of columns for the children of the given parent index.
        Here the number of columns will always be one."""
        return 1

    def data(self, index, role):
        """Returns the data stored under the given role for the item referred to by the index."""
        if not index.isValid():
            return None
        if role != QtCore.Qt.DisplayRole and role != QtCore.Qt.EditRole:
            return None

        item = index.internalPointer()

        return QVariant(repr(item))

    def index(self, row, column, parent):
        """
        Returns the index of the item in the model specified by the given row,
        column and parent index.
        Calls base class createIndex() to generate model indexes that other
        components can use to refer to items in this model.
        """
        # convert parent index to parent item
        item = parent.internalPointer() if parent.isValid() else self.root
        # get the respective child from the parent item
        child = item.child(row)

        return self.createIndex(row, column, child)

    def parent(self, index):
        """Returns the parent of the model item with the given index. If the item has
        no parent, an invalid QModelIndex is returned."""
        if not index.isValid():
            return QtCore.QModelIndex()

        child = index.internalPointer()
        parent = child.parent()

        if parent is self.root:
            return QtCore.QModelIndex()
        # get the index of parent
        row = parent.parent().row(parent)

        return self.createIndex(row, 0, parent)

    def rowCount(self, parent):
        """Returns the number of rows under the given parent index. When the parent is valid
        it means that rowCount is returning the number of children of parent."""
        item = parent.internalPointer() if parent.isValid() else self.root

        return len(item)


class RoiTreeWidget(QtGui.QTreeView):
    def __init__(self, parent, rois):
        QtGui.QTreeView.__init__(self, parent)

        self.model = RoiTreeModel(rois=rois, parent=self)
        self.setModel(self.model)

        # self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect(self.openMenu)
