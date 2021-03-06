#!/usr/bin/env python2
#
# Copyright 2015-2016 Carnegie Mellon University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import cv2
import dlib
import numpy as np
from numpy.linalg import inv
import os
import random
import shutil

import openface
import openface.helper
from openface.data import iterImgs

TEMPLATE = np.float32([
                       (0.0792396913815, 0.339223741112), (0.0829219487236, 0.456955367943),
                       (0.0967927109165, 0.575648016728), (0.122141515615, 0.691921601066),
                       (0.168687863544, 0.800341263616), (0.239789390707, 0.895732504778),
                       (0.325662452515, 0.977068762493), (0.422318282013, 1.04329000149),
                       (0.531777802068, 1.06080371126), (0.641296298053, 1.03981924107),
                       (0.738105872266, 0.972268833998), (0.824444363295, 0.889624082279),
                       (0.894792677532, 0.792494155836), (0.939395486253, 0.681546643421),
                       (0.96111933829, 0.562238253072), (0.970579841181, 0.441758925744),
                       (0.971193274221, 0.322118743967), (0.163846223133, 0.249151738053),
                       (0.21780354657, 0.204255863861), (0.291299351124, 0.192367318323),
                       (0.367460241458, 0.203582210627), (0.4392945113, 0.233135599851),
                       (0.586445962425, 0.228141644834), (0.660152671635, 0.195923841854),
                       (0.737466449096, 0.182360984545), (0.813236546239, 0.192828009114),
                       (0.8707571886, 0.235293377042), (0.51534533827, 0.31863546193),
                       (0.516221448289, 0.396200446263), (0.517118861835, 0.473797687758),
                       (0.51816430343, 0.553157797772), (0.433701156035, 0.604054457668),
                       (0.475501237769, 0.62076344024), (0.520712933176, 0.634268222208),
                       (0.565874114041, 0.618796581487), (0.607054002672, 0.60157671656),
                       (0.252418718401, 0.331052263829), (0.298663015648, 0.302646354002),
                       (0.355749724218, 0.303020650651), (0.403718978315, 0.33867711083),
                       (0.352507175597, 0.349987615384), (0.296791759886, 0.350478978225),
                       (0.631326076346, 0.334136672344), (0.679073381078, 0.29645404267),
                       (0.73597236153, 0.294721285802), (0.782865376271, 0.321305281656),
                       (0.740312274764, 0.341849376713), (0.68499850091, 0.343734332172),
                       (0.353167761422, 0.746189164237), (0.414587777921, 0.719053835073),
                       (0.477677654595, 0.706835892494), (0.522732900812, 0.717092275768),
                       (0.569832064287, 0.705414478982), (0.635195811927, 0.71565572516),
                       (0.69951672331, 0.739419187253), (0.639447159575, 0.805236879972),
                       (0.576410514055, 0.835436670169), (0.525398405766, 0.841706377792),
                       (0.47641545769, 0.837505914975), (0.41379548902, 0.810045601727),
                       (0.380084785646, 0.749979603086), (0.477955996282, 0.74513234612),
                       (0.523389793327, 0.748924302636), (0.571057789237, 0.74332894691),
                       (0.672409137852, 0.744177032192), (0.572539621444, 0.776609286626),
                       (0.5240106503, 0.783370783245), (0.477561227414, 0.778476346951)])

INV_TEMPLATE = np.float32([
                            (-0.04099179660567834, -0.008425234314031194, 2.575498465013183),
                            (0.04062510634554352, -0.009678089746831375, -1.2534351452524177),
                            (0.0003666902601348179, 0.01810332406086298, -0.32206331976076663)])

TPL_MIN, TPL_MAX = np.min(TEMPLATE, axis=0), np.max(TEMPLATE, axis=0)
MINMAX_TEMPLATE = (TEMPLATE - TPL_MIN) / (TPL_MAX - TPL_MIN)

class AlignDlib:
    """
    Use `dlib's landmark estimation <http://blog.dlib.net/2014/08/real-time-face-pose-estimation.html>`_ to align faces.

    The alignment preprocess faces for input into a neural network.
    Faces are resized to the same size (such as 96x96) and transformed
    to make landmarks (such as the eyes and nose) appear at the same
    location on every image.

    Normalized landmarks:

    .. image:: ../images/dlib-landmark-mean.png
    """

    #: Landmark indices corresponding to the inner eyes and bottom lip.
    INNER_EYES_AND_BOTTOM_LIP = [39, 42, 57]

    #: Landmark indices corresponding to the outer eyes and nose.
    OUTER_EYES_AND_NOSE = [36, 45, 33]

    def __init__(self, facePredictor):
        """
        Instantiate an 'AlignDlib' object.

        :param facePredictor: The path to dlib's
        :type facePredictor: str
        """
        assert facePredictor is not None

        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(facePredictor)

    def getAllFaceBoundingBoxes(self, rgbImg):
        """
        Find all face bounding boxes in an image.

        :param rgbImg: RGB image to process. Shape: (height, width, 3)
        :type rgbImg: numpy.ndarray
        :return: All face bounding boxes in an image.
        :rtype: dlib.rectangles
        """
        assert rgbImg is not None

        try:
            return self.detector(rgbImg, 1)
        except Exception as e:
            print("Warning: {}".format(e))
            # In rare cases, exceptions are thrown.
            return []

    def getLargestFaceBoundingBox(self, rgbImg):
        """
        Find the largest face bounding box in an image.

        :param rgbImg: RGB image to process. Shape: (height, width, 3)
        :type rgbImg: numpy.ndarray
        :return: The largest face bounding box in an image, or None.
        :rtype: dlib.rectangle
        """
        assert rgbImg is not None

        faces = self.getAllFaceBoundingBoxes(rgbImg)
        if len(faces) > 0:
            return max(faces, key=lambda rect: rect.width() * rect.height())
        else:
            return None

    def findLandmarks(self, rgbImg, bb):
        """
        Find the landmarks of a face.

        :param rgbImg: RGB image to process. Shape: (height, width, 3)
        :type rgbImg: numpy.ndarray
        :param bb: Bounding box around the face to find landmarks for.
        :type bb: dlib.rectangle
        :return: Detected landmark locations.
        :rtype: list of (x,y) tuples
        """
        assert rgbImg is not None
        assert bb is not None

        points = self.predictor(rgbImg, bb)
        return list(map(lambda p: (p.x, p.y), points.parts()))

    def align(self, imgDim, rgbImg, bb=None,
              landmarks=None, landmarkIndices=INNER_EYES_AND_BOTTOM_LIP):
        r"""align(imgDim, rgbImg, bb=None, landmarks=None, landmarkIndices=INNER_EYES_AND_BOTTOM_LIP)

        Transform and align a face in an image.

        :param imgDim: The edge length in pixels of the square the image is resized to.
        :type imgDim: int
        :param rgbImg: RGB image to process. Shape: (height, width, 3)
        :type rgbImg: numpy.ndarray
        :param bb: Bounding box around the face to align. \
                   Defaults to the largest face.
        :type bb: dlib.rectangle
        :param landmarks: Detected landmark locations. \
                          Landmarks found on `bb` if not provided.
        :type landmarks: list of (x,y) tuples
        :param landmarkIndices: The indices to transform to.
        :type landmarkIndices: list of ints
        :return: The aligned RGB image. Shape: (imgDim, imgDim, 3)
        :rtype: numpy.ndarray
        """
        assert imgDim is not None
        assert rgbImg is not None
        assert landmarkIndices is not None

        if bb is None:
            bb = self.getLargestFaceBoundingBox(rgbImg)
            if bb is None:
                return

        if landmarks is None:
            landmarks = self.findLandmarks(rgbImg, bb)

        npLandmarks = np.float32(landmarks)
        npLandmarkIndices = np.array(landmarkIndices)

        fidPoints = npLandmarks[npLandmarkIndices]
        templateMat = INV_TEMPLATE

        #create transformation matrix from output pixel coordinates to input pixel coordinates
        H = np.zeros((2,3), dtype=np.float32)
        for i in range(3):
            H[0][i] = fidPoints[0][0] * templateMat[0][i] + fidPoints[1][0] * templateMat[1][i] + fidPoints[2][0] * templateMat[2][i]
            H[1][i] = fidPoints[0][1] * templateMat[0][i] + fidPoints[1][1] * templateMat[1][i] + fidPoints[2][1] * templateMat[2][i]

        print H
        print fidPoints
        print npLandmarkIndices
        imgWidth = np.shape(rgbImg)[0]
        imgHeight = np.shape(rgbImg)[1]
        thumbnail = np.zeros((imgDim, imgDim,3), np.uint8)

        #interpolation from input image to output pixels using transformation mat H to compute
        #which input coordinates map to output
        for y in range(imgDim):
            for x in range(imgDim):
                xprime = x * H[0][1] + y * H[0][0] + H[0][2]
                yprime = x * H[1][1] + y * H[1][0] + H[1][2]
                tx = int(xprime)
                ty = int(yprime)
                horzOffset = 1
                vertOffset = 1
                if(tx < 0 or tx >= imgWidth or ty < 0 or ty >= imgHeight):
                    continue
                if(tx == imgWidth - 1):
                    horzOffset = 0
                if(ty == imgHeight - 1):
                    vertOffset = 0
                f1 = xprime - float(tx)
                f2 = yprime - float(ty)
                upperLeft = rgbImg[ty][tx]
                upperRight = rgbImg[ty][tx + horzOffset]
                bottomLeft = rgbImg[ty + vertOffset][tx]
                bottomRight = rgbImg[ty + vertOffset][tx + horzOffset]

                thumbnail[x][y][0] = upperLeft[0] * (1.0 - f1) * (1.0 - f2) + upperRight[0] * f1 * (1.0 - f2) + bottomLeft[0] * (1.0 - f1) * f2 + bottomRight[0] * f1 * f2
                thumbnail[x][y][1] = upperLeft[1] * (1.0 - f1) * (1.0 - f2) + upperRight[1] * f1 * (1.0 - f2) + bottomLeft[1] * (1.0 - f1) * f2 + bottomRight[1] * f1 * f2
                thumbnail[x][y][2] = upperLeft[2] * (1.0 - f1) * (1.0 - f2) + upperRight[2] * f1 * (1.0 - f2) + bottomLeft[2] * (1.0 - f1) * f2 + bottomRight[2] * f1 * f2

        return thumbnail

fileDir = os.path.dirname(os.path.realpath(__file__))
modelDir = os.path.join(fileDir, '..', 'models')
dlibModelDir = os.path.join(modelDir, 'dlib')
openfaceModelDir = os.path.join(modelDir, 'openface')


def write(vals, fName):
    if os.path.isfile(fName):
        print("{} exists. Backing up.".format(fName))
        os.rename(fName, "{}.bak".format(fName))
    with open(fName, 'w') as f:
        for p in vals:
            f.write(",".join(str(x) for x in p))
            f.write("\n")


def computeMeanMain(args):
    align = openface.AlignDlib(args.dlibFacePredictor)

    imgs = list(iterImgs(args.inputDir))
    if args.numImages > 0:
        imgs = random.sample(imgs, args.numImages)

    facePoints = []
    for img in imgs:
        rgb = img.getRGB()
        bb = align.getLargestFaceBoundingBox(rgb)
        alignedPoints = align.align(rgb, bb)
        if alignedPoints:
            facePoints.append(alignedPoints)

    facePointsNp = np.array(facePoints)
    mean = np.mean(facePointsNp, axis=0)
    std = np.std(facePointsNp, axis=0)

    write(mean, "{}/mean.csv".format(args.modelDir))
    write(std, "{}/std.csv".format(args.modelDir))

    # Only import in this mode.
    import matplotlib as mpl
    mpl.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.scatter(mean[:, 0], -mean[:, 1], color='k')
    ax.axis('equal')
    for i, p in enumerate(mean):
        ax.annotate(str(i), (p[0] + 0.005, -p[1] + 0.005), fontsize=8)
    plt.savefig("{}/mean.png".format(args.modelDir))


def alignMain(args):
    openface.helper.mkdirP(args.outputDir)

    imgs = list(iterImgs(args.inputDir))

    # Shuffle so multiple versions can be run at once.
    random.shuffle(imgs)

    if args.landmarks == 'outerEyesAndNose':
        landmarkIndices = openface.AlignDlib.OUTER_EYES_AND_NOSE
    elif args.landmarks == 'innerEyesAndBottomLip':
        landmarkIndices = openface.AlignDlib.INNER_EYES_AND_BOTTOM_LIP
    else:
        raise Exception("Landmarks unrecognized: {}".format(args.landmarks))

    align = AlignDlib(args.dlibFacePredictor)

    nFallbacks = 0
    for imgObject in imgs:
        print("=== {} ===".format(imgObject.path))
        outDir = os.path.join(args.outputDir, imgObject.cls)
        openface.helper.mkdirP(outDir)
        outputPrefix = os.path.join(outDir, imgObject.name)
        imgName = outputPrefix + ".png"

        if os.path.isfile(imgName):
            if args.verbose:
                print("  + Already found, skipping.")
        else:
            rgb = imgObject.getRGB()
            if rgb is None:
                if args.verbose:
                    print("  + Unable to load.")
                outRgb = None
            else:
                outRgb = align.align(args.size, rgb,
                                     landmarkIndices=landmarkIndices)
                if outRgb is None and args.verbose:
                    print("  + Unable to align.")

            if args.fallbackLfw and outRgb is None:
                nFallbacks += 1
                deepFunneled = "{}/{}.jpg".format(os.path.join(args.fallbackLfw,
                                                               imgObject.cls),
                                                  imgObject.name)
                shutil.copy(deepFunneled, "{}/{}.jpg".format(os.path.join(args.outputDir,
                                                                          imgObject.cls),
                                                             imgObject.name))

            if outRgb is not None:
                if args.verbose:
                    print("  + Writing aligned file to disk.")
                outBgr = cv2.cvtColor(outRgb, cv2.COLOR_RGB2BGR)
                cv2.imwrite(imgName, outBgr)

    if args.fallbackLfw:
        print('nFallbacks:', nFallbacks)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('inputDir', type=str, help="Input image directory.")
    parser.add_argument('--dlibFacePredictor', type=str, help="Path to dlib's face predictor.",
                        default=os.path.join(dlibModelDir, "shape_predictor_68_face_landmarks.dat"))

    subparsers = parser.add_subparsers(dest='mode', help="Mode")
    computeMeanParser = subparsers.add_parser(
        'computeMean', help='Compute the image mean of a directory of images.')
    computeMeanParser.add_argument('--numImages', type=int, help="The number of images. '0' for all images.",
                                   default=0)  # <= 0 ===> all imgs
    alignmentParser = subparsers.add_parser(
        'align', help='Align a directory of images.')
    alignmentParser.add_argument('landmarks', type=str,
                                 choices=['innerEyesAndBottomLip'],
                                 help='The landmarks to align to.')
    alignmentParser.add_argument(
        'outputDir', type=str, help="Output directory of aligned images.")
    alignmentParser.add_argument('--size', type=int, help="Default image size.",
                                 default=96)
    alignmentParser.add_argument('--fallbackLfw', type=str,
                                 help="If alignment doesn't work, fallback to copying the deep funneled version from this directory..")
    alignmentParser.add_argument('--verbose', action='store_true')

    args = parser.parse_args()

    if args.mode == 'computeMean':
        computeMeanMain(args)
    else:
        alignMain(args)

# Pode utilizar usando os dois métodos abaixo:

# ./util/align-dlib.py ./images/img_testes/ align outerEyesAndNose ./images/img_resultado/
# ./util/align-dlib.py ./images/pessoas_aprocessar/ align innerEyesAndBottomLip ./images/pessoas_crop_align/ --size 224
