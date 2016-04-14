from abc import abstractmethod

class Mask(object):
    """If a mask is mutable, it needs to provide a changed signal, which is supposed to be triggered upon modification."""

    def __init__(self,name = None):
        if name is None:
            self.name = type(self).__name__
        else:
            self.name = name

    @abstractmethod
    def __call__(self, data, mask):
        """Apply the mask on data"""
        raise NotImplementedError()
