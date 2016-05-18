import numpy


def template_matching(data, kernel, threshold):
    """
    Input $\mathbf{y}$ and $\mathbf{e}$ are two vectors, the normalized(todo: what means normalized?) template that should be used for matching and the data vector. Some intermediate values are:

    $$\overline{e} = \frac{1}{K}\sum_k e_k $$

    $$\overline{y_n} =  \frac{1}{K}\sum_K y_{n+k}$$

    The goal is to minimize the least squares distance:

    $$\chi_n^2(S,C)=\sum_K\left[y_{n+k} - (S e_k +C)\right]^2$$

    W.r.t. the variables $S$ and $C$. According to (ClementsBekkers, App. I)[1] the result is:

    $$S_n = \frac{\sum_k e_k y_{n+k}-1/K \sum_k e_k \sum_k y_{n+k}}{\sum e_k^2-1/K \sum_k e_k \sum_k e_k} = \frac{\sum_k e_k y_{n+k}-K\overline{e}\ \overline{y_n}}{\sum e_k^2-K\overline{e}^2} = $$

    and
    $$C_n = \overline{y_n} -S_n \overline{e}$$

    returns a named tuple:
        indices : the indices of detected events
        sse: the vector of squared errors used for comparison with the threshold
        s: the vector of optimal scaling parameters
        c: the vector of optimal offset parameters
        threshold: the threshold used for detection

    [1] http://dx.doi.org/10.1016%2FS0006-3495(97)78062-7
    """

    # use shortcuts as in formulas above
    y = data
    e = kernel

    # the size of the template
    N = len(e)

    # the sum over e (scalar)
    sum_e = numpy.sum(e)

    # the sum over e^2 (scalar<)
    sum_ee = numpy.sum(e ** 2)

    # the sum over blocks of y (vector of size N)
    sum_y = numpy.convolve(y, numpy.ones_like(e), mode='same')

    # the sum over blocks of y*y (vector of size N)
    sum_yy = numpy.convolve(y ** 2, numpy.ones_like(e), mode='same'
                            )
    # the sum_k  e_k y_{n+k}
    sum_ey = numpy.convolve(y, e, mode='same')

    # the optimal scaling factor
    s_n = (sum_ey - sum_e * sum_y / N) / (sum_ee - sum_e * sum_e / N)

    # the optimal offset
    c_n = (sum_y - s_n * sum_e) / N

    # the sum of squared errors when using optimal scaling and offset values
    sse_n = sum_yy + sum_ee * s_n ** 2 + N * c_n ** 2 - 2 * (s_n * sum_ey + c_n * sum_y - s_n * c_n * sum_e)

    # the detection criterion
    crit = s_n / (sse_n / (N - 1)) ** 0.5

    from collections import namedtuple

    result = namedtuple("ClementsBekkersResult", ['indices', 'crit', 's', 'c', 'threshold'])

    return result(indices=numpy.where(crit > threshold)[0], crit=crit, s=s_n, c=c_n, threshold=threshold)

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
