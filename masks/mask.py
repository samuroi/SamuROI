from abc import abstractmethod

class Mask(object):
    """If a mask is mutable, it needs to provide a changed signal, which is supposed to be triggered upon modification."""

    @abstractmethod
    def __call__(self, data, mask):
        """Apply the mask on data"""
        raise NotImplementedError()
