import numpy
import cv2


lk_params = dict( winSize  = (50, 50),
                  maxLevel = 3,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

feature_params = dict(maxCorners=300,
                       qualityLevel=0.01,
                       minDistance=40,
                       blockSize=30)

def draw_str(dst, (x, y), s):
    cv2.putText(dst, s, (x+1, y+1), cv2.FONT_HERSHEY_PLAIN, .5, (0, 0, 0), thickness = 2)
    cv2.putText(dst, s, (x, y), cv2.FONT_HERSHEY_PLAIN, .5, (255, 255, 255))

class Stabilization(object):
    def __init__(self, data = None):
        self.transformations = []
        if data is not None:
            self.run(data)

    def run(self, data, reference = None):
        if data.dtype != '>u1':
            data = (data > numpy.median(data)*1.3).astype('>u1')*255


        # TODO allow saving the stabilization process
        # vwriter = cv2.VideoWriter("/home/enigma/charite/dendrite_data/stabilization.avi",
        #                  cv2.VideoWriter_fourcc('X','V','I','D'),fps = 50,frameSize=(w,h), isColor = False)
        cv2.namedWindow('lk_track', flags=cv2.WINDOW_NORMAL)
        self.datashape = data.shape
        if reference is None:
            img0 = data[:, :, 0]
        else:
            img0 = reference
            assert img0.shape == data.shape[0:2]
        # p will have shape Nx1x2
        # TODO maybe adapt feature params if no good features were found
        p0 = cv2.goodFeaturesToTrack(img0, **feature_params)
        assert(p0.shape[0] > 0)
        for i in range(1, data.shape[2]):
            img1 = data[:, :, i]

            p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **lk_params)
            p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **lk_params)

            shift = (p0-p0r).reshape(-1, 2)
            d = (shift*shift).sum(axis=-1)

            dthreshold = .1
            while True:
                # get affine transform for good points
                good = d < dthreshold
                if good.sum() > 3: break
                else: dthreshold += 0.1

                if dthreshold > 0.3:
                    raise Exception("Cant find enough good features to track")

            p1g = p1[good]
            p0g = p0[good]

            # find the transformation between the frames
            tm = cv2.estimateRigidTransform(p1g, p0g, fullAffine=False)
            self.transformations.append(tm)

            img1 = cv2.warpAffine(img1, tm, dsize=img1.shape[::-1])
            # self.data[:,:,i] = img1

            copy = img1.copy()

            draw_str(copy, (20, 20), "Frame #:             %i" % i )
            draw_str(copy, (20, 40), "feature #:           %i" % p0.shape[0])
            draw_str(copy, (20, 60), "good feature #:      %i" % good.sum())
            draw_str(copy, (20, 80), "avg feature shift #: %4.2f/%4.2f/%4.2f" % (d.min(), d.mean(), d.max()))

            cv2.imshow('lk_track', copy)

            ch = 0xFF & cv2.waitKey(1)
            if ch == 27:
                break

        cv2.destroyWindow('lk_track')

    def apply(self, data, datashape=None):
        if datashape is not None:
            self.datashape = datashape
        """apply the found transformations to other data data wont be modified"""
        assert(data.shape == self.datashape)

        copy = data.astype(float)

        for i in range(1, data.shape[2]):
            frame = copy[:, :, i].copy()
            tm = self.transformations[i-1]
            copy[:, :, i] = cv2.warpAffine(frame, tm, dsize=frame.shape[::-1])
        return copy.astype(data.dtype)
