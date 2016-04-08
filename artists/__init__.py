from ..masks.branch import BranchMask
from .branch import BranchArtist

from ..masks.circle import CircleMask
from .circle import CircleArtist

from ..masks.polygon import PolygonMask
from .polygon import PolygonArtist

from ..masks.pixel import PixelMask
from .pixel import PixelArtist

from ..masks.segment import SegmentMask
from .segment import SegmentArtist

"""The mapping between mask and artist"""
artists = \
    {
        CircleMask: CircleArtist,
        BranchMask: BranchArtist,
        SegmentMask: SegmentArtist,
        PolygonMask: PolygonArtist,
        PixelMask: PixelArtist,
    }


def create_artist(mask):
    # select type from dictionary
    Artist = artists[type(mask)]
    # create artist with selected type
    return Artist(mask)
