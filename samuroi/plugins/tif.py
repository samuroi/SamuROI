import PIL
import numpy

def load_tif(filename):
    img = PIL.Image.open(filename)
    X,Y = img.size
    T = img.n_frames

    # workaround to get the dtype
    foo = numpy.array(img)

    data = numpy.ndarray(shape=(Y, X, T), dtype=foo.dtype)
    for i in range(T):
        img.seek(i)
        data[:, :, i] = numpy.array(img)
    return data
