__author__ = 'stephenlenzi'

import numpy as np
import cv2


def smooth_data(data, iterations=4):
    """smooth image stack
    ::param data: NxMxF ndarray, where F is the number of frames and NxM are the image dimensions
    ::param iterations: number of times to run the smoothing
    """
    # function for smoothing a single video
    sv = np.zeros_like(data)
    for i, d in enumerate(data.T):
        sv[:, :, i] = cv2.blur(d.T, (3, 3))
    iterations -= 1
    if iterations == 0:
        return sv
    else:
        sv = smooth_data(sv, iterations=iterations)
    return sv


def std_image(data):
    """::param data: NxMxF ndarray, where F is the number of frames and NxM are the image dimensions"""
    smoothed = smooth_data(data)  # generate smoothened NxMxF array
    std_image = np.std(smoothed, axis=2)
    return std_image


def sum_image(data):
    """::param data: NxMxF ndarray, where F is the number of frames and NxM are the image dimensions"""
    return np.sum(data, axis=2)
