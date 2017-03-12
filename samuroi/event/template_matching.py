import numpy


class ClementsBekkersResult(object):
    """
    Collection of results of least squares optimization for template matching.
    """
    def __init__(self, indices, crit, s, c, threshold, kernel):
        self.indices = indices
        """the indices of detected events, since zero padding is used for convolution, all indices need to get shifted by N/2 where N is the length of the kernel"""
        self.crit = crit
        """the criterion vector  used for comparison with the threshold"""
        self.s = s
        """the vector of optimal scaling parameters"""
        self.c = c
        """the vector of optimal offset parameters"""
        self.threshold = threshold
        """the threshold used for detection"""
        self.kernel = kernel
        """the kernel that was used for matching"""


def template_matching(data, kernel, threshold):
    r"""
    .. note::
            Threshold values usually should be in the range 1 to 5 for reasonable results.

    Input :math:`\mathbf{y}` and :math:`\mathbf{e}` are two vectors, the normalized(todo: what means normalized?)
    template that should be used for matching and the data vector. Some intermediate values are:

    :math:`\overline{e} = \frac{1}{K}\sum_k e_k`

    :math:`\overline{y_n} = \frac{1}{K}\sum_k y_{n+k}`

    The goal is to minimize the least squares distance:

    :math:`\chi_n^2(S,C)=\sum_K\left[y_{n+k} - (S e_k +C)\right]^2`

    W.r.t. the variables :math:`S` and :math:`C`. According to (ClementsBekkers, Appendix  I)[1] the result is:

    :math:`S_n = \frac{\sum_k e_k y_{n+k}-1/K \sum_k e_k \sum_k y_{n+k}}{\sum e_k^2-1/K \sum_k e_k \sum_k e_k} = \frac{\sum_k e_k y_{n+k}-K\overline{e}\ \overline{y_n}}{\sum e_k^2-K\overline{e}^2}`

    and

    :math:`C_n = \overline{y_n} -S_n \overline{e}`

    :param data: 1D numpy array with the timeseries to analyze, above denoted as :math:`\mathbf{y}`
    :param kernel: 1D numpy array with the template to use, above denoted as :math:`\mathbf{e}`
    :param threshold: scalar value usually between 4 to 5.
    :return: A result object :py:class:`samuroi.event.template_matching.ClementsBekkersResult`

    [1] http://dx.doi.org/10.1016%2FS0006-3495(97)78062-7
    """
    if len(data) <= len(kernel):
        raise Exception("Data length needs to exceed kernel length.")

    # use shortcuts as in formulas above
    y = data
    # reverse kernel, since we use convolve
    e = kernel[::-1]

    # the size of the template
    N = len(e)

    # the sum over e (scalar)
    sum_e = numpy.sum(e)

    # the sum over e^2 (scalar<)
    sum_ee = numpy.sum(e ** 2)

    # convolution mode
    # mode = 'full' # yields output of length N+M-1
    mode = 'same'  # yields output of length max(M,N)

    # the sum over blocks of y (vector of size N)
    sum_y = numpy.convolve(y, numpy.ones_like(e), mode=mode)

    # the sum over blocks of y*y (vector of size N)
    sum_yy = numpy.convolve(y ** 2, numpy.ones_like(e), mode=mode)
    # the sum_k  e_k y_{n+k}
    sum_ey = numpy.convolve(y, e, mode=mode)

    # the optimal scaling factor
    s_n = (sum_ey - sum_e * sum_y / N) / (sum_ee - sum_e * sum_e / N)

    # the optimal offset
    c_n = (sum_y - s_n * sum_e) / N

    # the sum of squared errors when using optimal scaling and offset values
    sse_n = sum_yy + sum_ee * s_n ** 2 + N * c_n ** 2 - 2 * (s_n * sum_ey + c_n * sum_y - s_n * c_n * sum_e)

    # the detection criterion
    crit = s_n / (sse_n / (N - 1)) ** 0.5

    from collections import namedtuple

    result = namedtuple("ClementsBekkersResult", ['indices', 'crit', 's', 'c', 'threshold', 'kernel'])

    return result(indices=numpy.where(crit > threshold)[0], crit=crit, s=s_n, c=c_n, threshold=threshold, kernel=kernel)

    # def least_squares(data, wavelet):
    #     """
    #     Convolve the given wavelet with the data and calculate the sum over the squared distance between data and wavelet for
    #     each data point. The returned array will show boundary effects since input data will be padded to match size S + W.
    #     The input wavelet should have positive time direction, i.e. it must not be flipped.
    #     Args:
    #         data: 1D array of shape S
    #         wavelet: 1D array of shape W
    #
    #     Returns: 1D array of shape S
    #     """
    #     # reverse the order of the wavelet, since we will use convolve instead of correlate
    #     wavelet = wavelet[::-1]
    #     # calculate sum_m S_{n+m}^2, this will have shape of S
    #     s1 = numpy.convolve(data * data, numpy.ones_like(wavelet), mode='same')
    #     # calculate wavelet normalization, this will be a scalar
    #     s2 = (wavelet * wavelet).sum()
    #     # calculate mixed term sum_m S_{n+m}*w_m
    #     s3 = numpy.convolve(data, wavelet, mode='same')
    #     return s1 + s2 - 2 * s3
    #
    #
    # def least_square_gradient(data,func,dfunc,width,shift = 0):
    #     """calulate the gradient of the sum of squares L_n(phi) for all n at given parameters phi,
    #     where n is the time index, and phi are the other paremters of the fit function.
    #     Returns:
    #         dL = partial L_n / partial n: discret gradient w.r.t. the index n (same shape as data)
    #         tuple holding the gradient w.r.t the other parameters phi
    #     """
    #     # TODO: replace convolve with correlate would allow to use the non reversed pulse shapes
    #     M = min(10*width,len(data))
    #     #print M
    #     wavelet = func(M, width,shift = shift)
    #     # the derivative of the wavelet w.r.t. width
    #     # TODO for multi parameter wavelets, this will be a tuple of derivatives w.r.t. the different parameters
    #     dwavelet = dfunc(M, width,shift = shift)[::-1]
    #     M = len(wavelet)
    #     #print M
    #     L = least_squares(data,func,width,shift = shift)
    #
    #     # calculate gradient of L w.r.t. n using the difference quotient (L_(n+1) - L_n) / (n+1-n)
    #     dn = numpy.gradient(L)
    #     # calculate gradient of L w.r.t. width
    #     # TODO for multi parameter wavelets, replace this with iteration over 1D gradients
    #     dw = -2.* numpy.convolve(data,dwavelet,mode = 'same') + 2*(wavelet*dwavelet).sum()
    #     return dn,dw
