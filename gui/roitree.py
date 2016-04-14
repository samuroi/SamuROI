from PyQt4 import QtCore, QtGui

from PyQt4.QtCore import QVariant, QObject, pyqtSignal


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

    def parent(self, mask=None):
        if mask is None:
            return None
        else:
            index = self.types.index(type(mask))
            return self.groups[index].parent(mask=mask)

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
        return self.items.index(child)

    def child(self, row):
        assert (len(self.items) > row)
        return self.items[row]

    def parent(self, mask=None):
        if mask is None:
            return self.__parent
        else:
            pass

    def __len__(self):
        return len(self.items)

    def __repr__(self):
        return "RoiGroup: " + str(self.type.__name__)


class RoiItem(TreeItem, QObject):
    mask_changed = pyqtSignal(object)

    def __init__(self, parent, mask):
        super(RoiItem, self).__init__(parent.masks)
        self.mask = mask
        self.children = []
        self.__parent = parent
        if hasattr(self.mask, "children"):
            for child in self.mask.children:
                self.children.append(RoiItem(parent=self, mask=child))
        if hasattr(self.mask, "changed"):
            # translate signal to qt signal in order to dispatch execution to gui event loop
            self.mask.changed.append(self.mask_changed.emit)
        self.mask_changed.connect(self.on_mask_changed)

    def on_mask_changed(self, mask):
        assert (mask is self.mask)

        # remove all children
        own_index = self.model.createIndex(self.parent().row(self), 0, self)
        self.model.beginRemoveRows(own_index, 0, len(self))
        self.children = []
        self.model.endRemoveRows()

        # add all children
        self.model.beginInsertRows(own_index, 0, len(mask.children))
        for child in mask.children:
            self.children.append(RoiItem(parent=self, mask=child))
        self.model.endInsertRows()
        self.model.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    @property
    def model(self):
        return self.__parent.model

    def row(self, child):
        if len(self.children) == 0:
            return None
        else:
            return self.children.index(child)

    def child(self, row):
        if len(self.children) == 0:
            return None
        else:
            return self.children[row]

    def __len__(self):
        return len(self.children)

    def parent(self):
        return self.__parent

    def __repr__(self):
        return self.mask.name


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

    def mask_to_index(self, mask):
        """return the model index of the given mask"""
        parentitem = self.root.parent(mask=mask)

        row = parentitem.row(mask=mask)

        return self.createIndex(row, 0, parentitem)

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


class RoiTreeWidget(QtGui.QTreeView):
    mask_selected = pyqtSignal(object)
    mask_deselected = pyqtSignal(object)

    def __init__(self, parent, rois, selection=None):
        QtGui.QTreeView.__init__(self, parent)
        self.rois = rois
        self.selection = selection

        self.model = RoiTreeModel(rois=rois, parent=self)
        # allow multi selection with shift and ctrl
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setModel(self.model)

        # self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect(self.openMenu)

        if selection is not None:
            self.selection.added.append(self.mask_selected.emit)
            self.selection.removed.append(self.mask_deselected.emit)

        self.mask_selected.connect(self.on_selected)
        self.mask_deselected.connect(self.on_deselected)

    def on_selected(self, mask):
        selectionmodel = self.selectionModel()

        # selectionmodel.select(index, QtGui.QItemSelectionModel.Select)

    def on_deselected(self, mask):
        selectionmodel = self.selectionModel()

        # selectionmodel.select(index, QtGui.QItemSelectionModel.Deselect)
