from __future__ import print_function

import numpy


class BiExponentialParameters(object):
    def __init__(self, tau1, tau2):  # , amplitude, baseline):
        assert (tau1 > 0)
        assert (tau2 > 0)
        # assert (tau2 > tau1)
        self._tau1 = tau1
        self._tau2 = tau2
        self._amplitude = 1.
        self._baseline = 0
        # self._amplitude = amplitude
        # self._baseline = baseline

    @property
    def tau1(self):
        return self._tau1

    @property
    def tau2(self):
        return self._tau2

    @property
    def amplitude(self):
        return self._amplitude

    @property
    def baseline(self):
        return self._baseline

    # @tau1.setter
    # def tau1(self, t):
    #     assert (t > 0)
    #     self._tau1 = t
    #
    # def tau2(self, t):
    #     assert (t > 0)
    #     self._tau2 = t

    def kernel(self, x=None):
        """ Create a kernel for the given parameters.
        x may be a numpy array to be used as support.
        If x is None, the support is chosen automatically such that the difference of the
        last value of the kernel and the baseline is less than 1%."""

        def biexp(x):
            p = self.amplitude * (numpy.exp(-x / self.tau1) - numpy.exp(-x / self.tau2))
            return p / numpy.max(p)

        if x is None:
            x = numpy.arange(10.)
            p = biexp(x)
            while p[-1] > 0.01:
                x = numpy.arange(len(x) * 2)
                p = biexp(x)
            return p + self.baseline
        else:
            p = biexp(x)
            if p[-1] > 0.01:
                print("Warning: support for biexp may be to small.")
            return p
