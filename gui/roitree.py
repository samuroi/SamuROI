from PyQt4 import QtCore, QtGui

from PyQt4.QtCore import QVariant, pyqtSignal


class TreeItem(object):
    def __init__(self, masks):
        super(TreeItem, self).__init__()
        self.masks = masks

    def child(self, row):
        raise NotImplementedError()

    def parent(self):
        raise NotImplementedError()

    def row(self, child):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()


class RootItem(TreeItem):
    def __init__(self, masks, model):
        TreeItem.__init__(self, masks)
        # the list of lists holding the rois
        self.model = model
        # store a list of types and respective roi groups
        # the list storage implies order which is good
        self.groups = []
        self.types = []

    def add_mask(self, mask):
        # check if we have a group for the type of the mask
        if type(mask) not in self.types:
            # root has no parent, hence use invalid index as parent
            self.model.beginInsertRows(QtCore.QModelIndex(), len(self), len(self))
            self.types.append(type(mask))
            self.groups.append(RoiGroupItem(parent=self, masks=self.masks, type=type(mask)))
            self.model.endInsertRows()
            self.model.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())
        # call on_added on child item
        index = self.types.index(type(mask))
        self.groups[index].add_mask(mask)

    def remove_mask(self, mask):
        # remove the mask from the respective child item
        index = self.types.index(type(mask))
        self.groups[index].remove_mask(mask)
        # check if there are still other items within the group
        if len(self.masks[type(mask)]) == 0:
            index = self.types.index(type(mask))
            # parentindex = self.model.createIndex(0, 0, self)
            # assert (parentindex.internalPointer() is self)
            self.model.beginRemoveRows(QtCore.QModelIndex(), index, index)
            del self.types[index]
            del self.groups[index]
            self.model.endRemoveRows()
            self.model.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def row(self, child):
        assert (type(child) is RoiGroupItem)
        return self.types.index(child.type)

    def child(self, row):
        assert (row < len(self.groups))
        return self.groups[row]

    def parent(self):
        return None

    def __len__(self):
        return len(self.groups)


class RoiGroupItem(TreeItem):
    def __init__(self, parent, masks, type):
        TreeItem.__init__(self, masks)
        # keep items in list to preserve order
        self.items = []
        self.type = type
        self.__parent = parent

    @property
    def model(self):
        return self.__parent.model

    def add_mask(self, mask):
        assert (type(mask) is self.type)
        rootindex = self.model.createIndex(0, 0, self.parent())
        parentindex = self.model.index(self.parent().types.index(self.type), 0, rootindex)
        assert (parentindex.internalPointer() is self)
        # assert (parentindex.parent().internalPointer() is self.parent())
        self.model.beginInsertRows(rootindex, len(self), len(self))
        self.items.append(RoiItem(parent=self, mask=mask))
        self.model.endInsertRows()
        self.model.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def remove_mask(self, mask):
        assert (type(mask) is self.type)
        maskindex = [i.mask for i in self.items].index(mask)
        rootindex = self.model.createIndex(0, 0, self.parent())
        parentindex = self.model.index(self.parent().types.index(self.type), 0, rootindex)
        assert (parentindex.internalPointer() is self)
        # assert (parentindex.parent().internalPointer() is self.parent())
        self.model.beginRemoveRows(rootindex, maskindex, maskindex)
        del self.items[maskindex]
        self.model.endRemoveRows()
        self.model.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def row(self, child):
        return self.items.index(child.item)

    def child(self, row):
        assert (len(self.items) > row)
        return self.items[row]

    def parent(self):
        return self.__parent

    def __len__(self):
        return len(self.items)

    def __repr__(self):
        return "RoiGroup: " + str(self.type.__name__)


class RoiItem(TreeItem):
    def __init__(self, parent, mask):
        super(RoiItem, self).__init__(parent.masks)
        self.mask = mask
        self._parent = parent

    def row(self, child):
        return None

    def child(self, row):
        return None

    def __len__(self):
        return 0

    def parent(self):
        return self._parent


class RoiTreeModel(QtCore.QAbstractItemModel):
    mask_added = pyqtSignal(object)
    mask_removed = pyqtSignal(object)

    def __init__(self, rois, parent=None):
        super(RoiTreeModel, self).__init__(parent)
        self.root = RootItem(masks=rois, model=self)
        self.masks = rois
        # notify the data tree about changes, to do this, proxy the events into the qt event loop
        self.masks.added.append(self.mask_added.emit)
        self.masks.removed.append(self.mask_removed.emit)
        # now connect to the own signals
        self.mask_added.connect(self.root.add_mask)
        self.mask_removed.connect(self.root.remove_mask)

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

        childindex = self.createIndex(row, column, child)
        # assert(childindex.parent() == parent)
        return childindex

    def parent(self, index):
        """Returns the parent of the model item with the given index. If the item has
        no parent, an invalid QModelIndex is returned."""
        item = index.internalPointer() if index.isValid() else self.root

        if item is self.root:
            return QtCore.QModelIndex()
        elif item.parent() is self.root:
            return self.createIndex(0, 0, self.root)
        else:
            # careful here: we don't want the row of item in item.parent(),
            # but the row of item.parent() in item.parent().parent()
            row = item.parent().parent().row(item.parent())

            return self.createIndex(row, 0, item.parent())

    def rowCount(self, parent):
        """Returns the number of rows under the given parent index. When the parent is valid
        it means that rowCount is returning the number of children of parent."""
        item = parent.internalPointer() if parent.isValid() else self.root

        return len(item)

        # def insertRows(self,row,count,parent):
        #     """
        #     inserts count rows into the model before the given row. Items in the new row will be children of the item represented by the parent model index.
        #     Args:
        #         row: int
        #         count:  int
        #         parent: qmodelindex
        #
        #     Returns:
        #
        #     """
        #     self.beginInsertRows(QModelIndex(), position, position+c-1);
        #
        #     rows += c;
        #
        #     endInsertRows();
        #     return true;


class RoiTreeWidget(QtGui.QTreeView):
    def __init__(self, parent, rois):
        QtGui.QTreeView.__init__(self, parent)

        self.model = RoiTreeModel(rois=rois, parent=self)
        self.setModel(self.model)

        # self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect(self.openMenu)
