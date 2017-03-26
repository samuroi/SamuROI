__author__ = 'stephenlenzi'

import sys
import numpy as np
from scipy import ndimage
from skimage import segmentation


class MaskGenerator(object):
    """
    Parent class for generating masklists and manually correcting them
    """
    def __init__(self, blob_image, raw_image, center_of_mass=None):

        self.raw_image = raw_image
        self.blob_image = blob_image

        if center_of_mass is None:
            self.center_of_mass = get_centers_of_mass_from_blobs(self.blob_image)
        else:
            self.center_of_mass = center_of_mass

        self.putative_nuclei_image, _ = remove_small_blobs(self.blob_image, self.center_of_mass)  # remove non-overlapping centers

    def append_com(self, c):
        x = self.center_of_mass.tolist()
        x.append(c)
        self.center_of_mass = np.array(x)

    def remove_com(self, c):
        x = self.center_of_mass.tolist()
        x.remove(c)
        self.center_of_mass = np.array(x)

    def update(self):
        pass

    def create_roi_masks(self, seg_type):
        pass


class DonutCells(MaskGenerator):
    """
    Child class to handle GCaMP data - i.e. donut shaped rois, with a dark nucleus
    """
    def __init__(self, raw_image, putative_nuclei_image, putative_somata_image, center_of_mass=None):
        super(DonutCells, self).__init__(putative_nuclei_image, raw_image, center_of_mass)
        self.putative_somata_image = putative_somata_image
        self.putative_nuclei_image = ndimage.binary_fill_holes(self.putative_nuclei_image)
        self.watershed_image = np.logical_or(self.putative_nuclei_image, self.putative_somata_image)
        self.segmentation_labels = calculate_distance(self.watershed_image, self.center_of_mass)
        self.labelled_nuclei = calculate_distance(self.putative_nuclei_image, self.center_of_mass)
        self.roi_masks = create_roi_masks(self.center_of_mass, self.putative_nuclei_image, self.putative_somata_image)

    def update(self):
        self.putative_nuclei_image, _ = remove_small_blobs(self.putative_nuclei_image, self.center_of_mass)
        self.segmentation_labels = calculate_distance(self.watershed_image, self.center_of_mass)
        self.roi_masks = create_roi_masks(self.center_of_mass, self.putative_nuclei_image, self.putative_somata_image)


class BlobCells(MaskGenerator):
    """
    Child class for blob cells - i.e. bolus loaded cells. Nucleus also fluorescent
    """

    def __init__(self, segmentation_layer, raw_image):
        super(BlobCells, self).__init__(segmentation_layer, raw_image)
        self.watershed_image = self.putative_nuclei_image
        self.segmentation_labels = calculate_distance(self.watershed_image, self.center_of_mass)
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
    ::returns com: a np ndarray of x,y coordinates for the center of each target object

    """

    segmentation_layer = ndimage.binary_opening(segmentation_layer, iterations=iterations)  # remove small objects
    labels, label_number = ndimage.measurements.label(segmentation_layer)  # label remaining blobs

    com = np.zeros((label_number, 2))

    for i in range(label_number):
        idx = np.where(labels == i+1)  # calculate the center of mass for each blob
        com[i, 1] = np.mean(idx[1].astype(float))  # must be float
        com[i, 0] = np.mean(idx[0].astype(float))  # must be float

    return com


def remove_small_blobs(segmentation_layer, com):
    """
    removes non-overlapping pixel-islands and cell centres (coms)
    :param segmentation_layer: NxM ndarray image mask of all target objects
    :param com: a np ndarray of x,y coordinates for the center of each target object
    :return updated_labels:
    """
    labels, label_number = ndimage.label(segmentation_layer)  # label all pixel islands
    updated_labels = np.zeros_like(labels)
    coms_to_keep = np.zeros(len(com))  # holder

    for i in range(label_number):
        idx = np.where(labels == i+1)
        for j, c in enumerate(com.astype(int)):
            if labels[c[0], c[1]] == i+1:  # if the com is in the blob
                updated_labels[idx] = 1  # add the blob
                coms_to_keep[j] = 1  # add the com

    com_index = np.where(coms_to_keep == 1)
    updated_com = com[com_index]

    return updated_labels, updated_com


def calculate_distance(com, image):
    """
    takes the centers of each blob, and an image to be segmented. Divides the image according to the center of masses
    by a random walk

    :param image: a binarised image to be segmented
    :param com: the centres that will define the maxima of the watershed segmentation
    :return segmentation_labels: a labelled image/segmentation, where each index belongs do a different center of mass

    """
    # random walk segmentation of 2D image-mask array
    distance = ndimage.distance_transform_edt(np.abs(image-1))
    local_maxi = np.zeros_like(image)

    for c in com:
        local_maxi[int(c[0]), int(c[1])] = 1

    markers = ndimage.label(local_maxi)[0]
    segmentation_labels = segmentation.random_walker(distance, markers, beta=60)

    return segmentation_labels


def blob_labels(com, blob_image):
    """
    label nuclei with segmentation - so labels are in the same order as the outer layer
    """

    image = np.abs(blob_image-1)
    distance = ndimage.distance_transform_edt(np.abs(image-1))
    local_maxi = np.zeros_like(image)
    for c in com:
        local_maxi[int(c[0]), int(c[1])] = 1
    markers = ndimage.label(local_maxi)[0]
    segmented_blobs = segmentation.random_walker(distance, markers, beta=20)

    return segmented_blobs, distance


def create_roi_masks(com, putative_nuclei_image, putative_somata_image=None, radius=3):
        """
        create roi masks for the outer segment of the cell (i.e. soma)
        ::param radius: limits the size of the mask
        """
        roi_mask_list = []

        if putative_somata_image is None:
            putative_somata_image = np.zeros_like(putative_nuclei_image)
        putative_nuclei_image = remove_small_blobs(putative_nuclei_image,com)[0]
        watershed_image = np.logical_or(putative_nuclei_image, putative_somata_image)
        labelled_watershed = calculate_distance(watershed_image, com)
        labelled_putative_somata = putative_somata_image*labelled_watershed
        labelled_putative_nuclei = calculate_distance(putative_nuclei_image,
                                                      com)*putative_nuclei_image  # nuclei need their own watershed

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
