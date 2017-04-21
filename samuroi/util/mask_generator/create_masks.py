__author__ = 'stephenlenzi'

import sys
import numpy as np
from scipy import ndimage
from skimage import segmentation


class MaskGenerator(object):
    """
    Parent class for generating mask lists and manually correcting them
    """
    def __init__(self, blob_image, raw_image, centers_of_mass=None):

        self.raw_image = raw_image
        self.blob_image = blob_image

        if centers_of_mass is None:
            self.centers_of_mass = get_centers_of_mass_from_blobs(self.blob_image)
        else:
            self.centers_of_mass = centers_of_mass

        self.putative_nuclei_image, _ = remove_small_blobs(self.centers_of_mass, self.blob_image)  # remove non-overlapping centers

    def append_center_of_mass(self, c):
        x = self.centers_of_mass.tolist()
        x.append(c)
        self.centers_of_mass = np.array(x)

    def remove_center_of_mass(self, c):
        x = self.centers_of_mass.tolist()
        x.remove(c)
        self.centers_of_mass = np.array(x)

    def update(self):
        pass

    def create_roi_masks(self, seg_type):
        pass


class DonutCells(MaskGenerator):
    """
    Child class to handle GCaMP data - i.e. donut shaped rois, with a dark nucleus
    """
    def __init__(self, raw_image, putative_nuclei_image, putative_somata_image, centers_of_mass=None):
        super(DonutCells, self).__init__(putative_nuclei_image, raw_image, centers_of_mass)
        self.putative_somata_image = putative_somata_image
        self.putative_nuclei_image = ndimage.binary_fill_holes(self.putative_nuclei_image)
        self.watershed_image = np.logical_or(self.putative_nuclei_image, self.putative_somata_image)
        self.segmentation_labels = calculate_distance(self.centers_of_mass, self.watershed_image)
        self.labelled_nuclei = calculate_distance(self.centers_of_mass, self.putative_nuclei_image)
        self.roi_masks = create_roi_masks(self.centers_of_mass, self.putative_nuclei_image, self.putative_somata_image)

    def update(self):
        self.putative_nuclei_image, _ = remove_small_blobs(self.centers_of_mass, self.putative_nuclei_image)
        self.segmentation_labels = calculate_distance(self.centers_of_mass, self.watershed_image)
        self.roi_masks = create_roi_masks(self.centers_of_mass, self.putative_nuclei_image, self.putative_somata_image)


class BlobCells(MaskGenerator):
    """
    Child class for blob cells - i.e. bolus loaded cells. Nucleus also fluorescent
    """

    def __init__(self, segmentation_layer, raw_image):
        super(BlobCells, self).__init__(segmentation_layer, raw_image)
        self.watershed_image = self.putative_nuclei_image
        self.segmentation_labels = calculate_distance(self.centers_of_mass, self.watershed_image)
        self.roi_mask_list = self.create_roi_masks()

    def create_roi_masks(self):
        roi_mask_list = []
        for i in range(np.max(self.segmentation_labels)):
            idx = np.where(self.segmentation_labels*self.putative_nuclei_image == i+1)
            x = np.vstack((idx[0], idx[1]))
            m = np.reshape(x.T, (len(idx[0]), 2))
            roi_mask_list.append(m)

        return roi_mask_list


def get_centers_of_mass_from_blobs(segmentation_layer, iterations=3):
    """
    Determine the centers of each object in an image

    ::param segmentation_layer: NxM ndarray image mask of all target objects
    ::param iterations: threshold for removal of small non-target objects
    ::return centers_of_mass: a np ndarray of x,y coordinates for the center of each target object

    """

    segmentation_layer = ndimage.binary_opening(segmentation_layer, iterations=iterations)  # remove small objects
    labels, label_number = ndimage.measurements.label(segmentation_layer)  # label remaining blobs

    centers_of_mass = np.zeros((label_number, 2))

    for i in range(label_number):
        idx = np.where(labels == i+1)  # calculate the center of mass for each blob
        centers_of_mass[i, 1] = np.mean(idx[1].astype(float))  # must be float
        centers_of_mass[i, 0] = np.mean(idx[0].astype(float))  # must be float

    return centers_of_mass


def remove_small_blobs(centers_of_mass, segmentation_layer):
    """
    removes non-overlapping pixel-islands and cell centres (centers_of_mass)
    :param segmentation_layer: NxM ndarray image mask of all target objects
    :param centers_of_mass: a np ndarray of x,y coordinates for the center of each target object
    :return updated_labels:
    """
    labels, label_number = ndimage.label(segmentation_layer)  # label all pixel islands
    updated_labels = np.zeros_like(labels)
    centers_of_mass_to_keep = np.zeros(len(centers_of_mass))  # holder

    for i in range(label_number):
        idx = np.where(labels == i+1)
        for j, c in enumerate(centers_of_mass.astype(int)):
            if labels[c[0], c[1]] == i+1:  # if the center_of_mass is in the blob
                updated_labels[idx] = 1  # add the blob
                centers_of_mass_to_keep[j] = 1  # add the center_of_mass

    centers_of_mass_idx = np.where(centers_of_mass_to_keep == 1)
    updated_centers_of_mass = centers_of_mass[centers_of_mass_idx]

    return updated_labels, updated_centers_of_mass


def calculate_distance(centers_of_mass, image):
    """
    takes the centers of each blob, and an image to be segmented. Divides the image according to the center of masses
    by a random walk

    :param image: a binarised image to be segmented
    :param centers_of_mass: the centres that will define the maxima of the watershed segmentation
    :return segmentation_labels: a labelled image/segmentation, where each index belongs do a different center of mass

    """
    # random walk segmentation of 2D image-mask array
    distance = ndimage.distance_transform_edt(np.abs(image-1))
    local_maxi = np.zeros_like(image)

    for c in centers_of_mass:
        local_maxi[int(c[0]), int(c[1])] = 1

    markers = ndimage.label(local_maxi)[0]
    segmentation_labels = segmentation.random_walker(distance, markers, beta=60)

    return segmentation_labels


def blob_labels(centers_of_mass, blob_image):
    """
    label nuclei with segmentation - so labels are in the same order as the outer layer

    :param list centers_of_mass: centers of target blobs/cells
    :param np.array blob_image: image of the target cells, or nuclei of cells
    :return segmented_blobs: a labelled image where each index is a different cell
    :return distance: image where each pixel's value is related to how far away from a blob center it is
    """

    image = np.abs(blob_image-1)
    distance = ndimage.distance_transform_edt(np.abs(image-1))
    local_maxi = np.zeros_like(image)
    for c in centers_of_mass:
        local_maxi[int(c[0]), int(c[1])] = 1
    markers = ndimage.label(local_maxi)[0]
    segmented_blobs = segmentation.random_walker(distance, markers, beta=20)

    return segmented_blobs, distance


def create_roi_masks(centers_of_mass, putative_nuclei_image, putative_somata_image=None, radius=3):
        """
        create roi masks for the outer segment of the cell (i.e. soma)

        :param radius: limits the size of the mask
        :return roi_mask_list: a list of pixels for each cell, for further analysis
        """
        roi_mask_list = []

        if putative_somata_image is None:
            putative_somata_image = np.zeros_like(putative_nuclei_image)
        putative_nuclei_image = remove_small_blobs(centers_of_mass, putative_nuclei_image)[0]
        watershed_image = np.logical_or(putative_nuclei_image, putative_somata_image)
        labelled_watershed = calculate_distance(centers_of_mass, watershed_image)
        labelled_putative_somata = putative_somata_image*labelled_watershed
        labelled_putative_nuclei = calculate_distance(centers_of_mass, putative_nuclei_image)*putative_nuclei_image  # nuclei need their own watershed

        for i in range(np.max(labelled_putative_somata)):  # for each nucleus

            # calculate the distance away from the nucleus boundary

            distance_from_blob_centre = ndimage.distance_transform_edt(labelled_putative_nuclei != i+1)
            bool_mask = np.ones_like(labelled_putative_nuclei)
            bool_mask[distance_from_blob_centre > radius] = 0
            bool_mask[distance_from_blob_centre == 0] = 0

            # take all indices within the radius number of pixels of the nucleus boundary

            idx = np.where(labelled_putative_somata*bool_mask == i+1)
            x = np.vstack((idx[0], idx[1]))
            m = np.reshape(x.T, (len(idx[0]), 2))
            roi_mask_list.append(m)

        return roi_mask_list
