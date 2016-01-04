
class RoiGroup(bicycle):
    """
    Encapsule a group of rois
    """
    def __init__(self,items = None):
        items = [] if items is None else items
        super(RoiGroup,self).__init__(items)
        self.__active = None

    @property
    def active(self):
        """Return either the active roi of this group, or None if there is no active roi."""
        return self.__active

    @active.setter
    def active(self,p):
        bevore = self.active
        if self.active is not None:
            self.active.active = False

        assert(p in self.items or p is None)

        self.__active = p
        if self.active is not None:
            self.active = True

        if bevore is not p:
            self.draw()

    def next(self):
        self.active = bicycle.next(self)

    def previous_polymask(self):
        self.active = bicycle.next(self)

    def append(self,roi):
        self.items.append(roi)
        self.active = self.items[-1]

    def remove(self,p = None):
        if p is None:
            p = self.active
        if p is None:
            return
        self.next()
        p.remove()
        self.items.remove(p)
        self.draw()
