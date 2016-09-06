import numpy
import scipy.signal


class DetrendPostProcessor(object):
    """Simple linear detrend based on scipy.signal.detrend."""

    def __call__(self, trace):
        if not numpy.isinf(trace).any() and not numpy.isnan(trace).any():
            return scipy.signal.detrend(trace)
        return trace


class MovingAveragePostProcessor(object):
    def __init__(self, N):
        """ N: The size of averaging window. """
        self.N = N

    def __call__(self, trace):
        return numpy.convolve(trace, numpy.ones(shape=self.N), mode='same') / self.N


class PostProcessorPipe(object):
    """Allow to concatenate multiple postprocessors."""

    def __init__(self, iterable=[]):
        self.__processors = []
        for i in iterable:
            self.__processors.append(i)

    def __call__(self, trace):
        for p in self.__processors:
            trace = p(trace)
        return trace

    def append(self, pp):
        """Append a processor to the end of the pipe."""
        self.__processors.append(pp)
