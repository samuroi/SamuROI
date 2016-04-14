from .mask import Mask

from ..util.branch import Branch


class SegmentMask(Branch, Mask):
    def __init__(self, data, parent):
        super(SegmentMask, self).__init__(data)
        self.parent = parent

        from .polygon import PolygonMask
        self.__polygon = PolygonMask(corners=self.outline)

    def __call__(self, data, mask):
        return self.__polygon(data, mask)

    def split(self, nsegments=2, length=None, k=1, s=0):
        """Split the segment in n equal parts, and adopt the parent branch accordingly."""

        # get the index of the old segment in the parents child list
        i = self.parent.segments.index(self)

        # split segment and convert new branch objects into segments
        subsegments = [SegmentMask(data=s.data, parent=self.parent)
                       for s in Branch.split(self, nsegments=nsegments, length=length, k=k, s=s)]

        # insert new items into list at correct position, i.e. replace self
        self.parent.segments[i:i + 1] = subsegments
        # trigger parents changed signal
        self.parent.changed()

    def join(self, next=True):
        """
        Join two segments into one. Arguments:
            next:    True or False, denote whether to join the segment with the preceeding or succeeding one.
        """

        # the list of children of the parent
        children = self.parent.segments

        # get the index of the segment in the parents child list
        i = children.index(self)

        # select the slice of the two segments to join
        # this will work event for i = 0,1,len(childrens)-1 and len(childrens)
        s = slice(i, i + 2) if next else slice(i - 1, i + 1)

        # we cant join next/previous, if there is no respective other segment
        if len(children[s]) < 2:
            return
        # get handle on the two children to join
        child0, child1 = children[s]

        # create joined segment
        joined = Branch.append(child0, child1)

        # replace the two old ones in list
        children[s] = [SegmentMask(data=joined.data, parent=self.parent)]

        self.parent.changed()
