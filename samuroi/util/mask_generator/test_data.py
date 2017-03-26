__author__ = 'stephenlenzi'

import numpy as np


def create_test_dataset(image_shape, n, circle_radius, donut_radius):
    img = np.zeros((image_shape[0], image_shape[1]))
    y_pixels = np.arange(0, image_shape[0], 1)
    x_pixels = np.arange(0, image_shape[1], 1)
    cell_y_coords = np.random.choice(y_pixels, n, replace=False)
    cell_x_coords = np.random.choice(x_pixels, n, replace=False)

    for x, y in zip(cell_x_coords, cell_y_coords):
        xx, yy = np.mgrid[:512, :512]  # create mesh grid of image dimensions
        circle = (xx - x) ** 2 + (yy - y) ** 2  # apply circle formula
        donut = np.logical_and(circle < (circle_radius+donut_radius),
                               circle > (circle_radius-5))  # donuts are thresholded circles
        thresholded_circle = circle < circle_radius
        img[np.where(thresholded_circle)] = 1
        img[np.where(donut)] = 2
    return img
