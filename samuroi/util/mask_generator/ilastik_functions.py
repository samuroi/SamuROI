__author__ = 'stephenlenzi'

import os
import h5py
import numpy as np
import tempfile
import subprocess


"""These are for running ilastik in headless mode within Python"""


def get_ilastik_project_path():
    for f in os.listdir("./"):
        if f[-4:] == '.ilp':
            return f
        raise IOError('ilastik project file not found')


def ilastik_segment(data, ilastik_path, ilastik_project_path=None):
    """
    Convert image data into a segmentation using ilastik. It requires that you have created a project file
    specifically for the type of images you want to classify. If this function fails, you should first verify that
    ilastik is able to form a segmentation when you add the image to the project file as you may need to train
    the algorithm more.

    :param data: NxM array, NxM is image shape.
    :param ilastik_path: path to ilastik installation (should be named something like run_ilastik.sh)
    :param ilastik_project_path:  path to ilastik project file (user must create this in ilastik)

    example usage:

    ..code block:: python
        >>> ilastik_path = './ilastik-release/run_ilastik.sh'
        >>> ilastik_project_path = './data/GCaMP.ilp'
        >>> simple_segmentation = ilastik_segment(data, ilastik_path, ilastik_project_path)
        >>>
    """

    if ilastik_project_path is None:  # defaults to any .ilp file it finds in the home directory
        ilastik_project_path = get_ilastik_project_path()

    tmp_data = tempfile.NamedTemporaryFile()  # temporary file is created
    np.save(tmp_data.name, data)  # input data is saved because ilastik works with files

    tmp_img = tempfile.NamedTemporaryFile()  # temporary file created for ilastik output file

    # set filepaths for ilastik
    input_image_path = tmp_data.name + '.npy'
    output_image_path = tmp_img.name

    if not os.path.isfile(input_image_path):
        raise IOError('failed to create input image file')

    if not _check_tmp_file_equals_data(input_image_path, data):
        raise IOError('input image not the same as data')

    # call ilastik in headless mode (i.e. without opening the user interface)
    subprocess.call([ilastik_path, "--headless",  # headless ilastik classification saves segmentation
                     "--project=" + ilastik_project_path,
                     "--output_filename_format=" + output_image_path,
                     input_image_path,
                     "--export_source=Simple Segmentation"])

    if not os.path.isfile(output_image_path):
        raise IOError('output image not found')

    # load the newly generated image
    simple_segmentation = h5py.File(tmp_img.name + '.h5', 'r')["exported_data"].value[:, :, 0]

    # close the temporary files (resulting in their deletion)
    tmp_img.close()
    tmp_data.close()

    return simple_segmentation


def _check_tmp_file_equals_data(temp_file, data):
    temp_file_data = np.load(temp_file)
    return temp_file_data.all() == data.all()
