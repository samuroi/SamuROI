from .polyroi import PolygonRoi

from .polyroi import PolygonRoi


class SegmentRoi(PolygonRoi):

    def __init__(self, data, axes, parent, **kwargs):
        super(SegmentRoi,self).__init__(data = data, axes = axes, **kwargs)
        self.parent = parent

    def split(self, nsegments):
        """Split the segment in n equal parts, and adopt the parent branch accordingly."""

        # remove the old polygon artist
        self.artist.remove()

        # get the index of the old segment in the parents child list
        i = self.parent.children.index(segment)

        # split segment and convert new branch objects into segments
        subsegments = [SegmentRoi(data = s.data,
                               parent = self.parent,
                               axes = self.axes)
                            for s in super(SegmentRoi, self).split(nsegments = nsegments)]

        self.parent.children[i:i+1] = subsegments


    def join(self, next = True):
        """
        Join two segments into one. Arguments:
            next:    True or False, denote whether to join the segment with the preceeding or succeeding one.
        """

        # the list of childrens of the parent
        children = self.parent.children

        # get the index of the segment in the parents child list
        i = children.index(self)

        # select the slice of the two segments to join
        # this will work event for i = 0,1,len(childrens)-1 and len(childrens)
        s = slice(i,i+2) if next else slice(i-1,i+1)

        # we cant join next/previous, if there is no respective other segment
        if len(children[s])<2:
            return

        # remove the old artists
        for child in children[s]:
            child.artist.remove()

        # create joined segment
        joined = children[s][0].append(children[s][1])
        # convert the plain branch into Branch+Artist class
        joined = SegmentRoi(data = joined.data,
                         parent = self.parent,
                         axes = self.axes)
        # replace the two old ones in list
        children[s] = [joined]

        return joined
