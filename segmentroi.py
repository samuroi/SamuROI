
from .branch  import Branch
from .polyroi import PolygonRoi


class SegmentRoi(Branch,PolygonRoi):

    def __init__(self, branch, datasource, axes, parent, **kwargs):
        Branch.__init__(self, data = branch)
        PolygonRoi.__init__(self, outline = self.outline, datasource = datasource, axes = axes, **kwargs)
        #super(SegmentRoi,self).__init__(data = data, axes = axes, **kwargs)
        self.parent = parent

    def split(self, nsegments):
        """Split the segment in n equal parts, and adopt the parent branch accordingly."""

        # remember the holdaxes
        holdaxes = [] + self.holdaxes

        # remove the old polygon artist
        self.remove()

        # get the index of the old segment in the parents child list
        i = self.parent.children.index(self)

        # split segment and convert new branch objects into segments
        subsegments = [SegmentRoi(branch = s.data,
                                  datasource = self.datasource,
                                  parent = self.parent,
                                  axes = self.axes)
                            for s in super(SegmentRoi, self).split(nsegments = nsegments)]

        for ax in holdaxes:
            for ss in subsegments:
                ss.toggle_hold(ax)

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

        # remember the hold axes
        holdaxes = set(children[s][0].holdaxes + children[s][1].holdaxes)

        # remove the old artists
        for child in children[s]:
            child.remove()

        # create joined segment
        joined = children[s][0].append(children[s][1])
        # convert the plain branch into Branch+Artist class
        joined = SegmentRoi(branch = joined.data,
                            datasource = self.datasource,
                            parent = self.parent,
                            axes = self.axes)
        # replace the two old ones in list
        children[s] = [joined]

        for ax in holdaxes:
            joined.toggle_hold(ax)

        return joined
