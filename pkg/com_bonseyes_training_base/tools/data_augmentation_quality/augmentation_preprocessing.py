# owned by nViso or its suppliers or licensors.  Title to the  Material remains
# with nViso SA or its suppliers and licensors. The Material contains trade
# secrets and proprietary and confidential information of nViso or its
# suppliers and licensors. The Material is protected by worldwide copyright and trade
# secret laws and treaty provisions. You shall not disclose such Confidential
# Information and shall use it only in accordance with the terms of the license
# agreement you entered into with nViso.
#
# NVISO MAKES NO REPRESENTATIONS OR WARRANTIES ABOUT THE SUITABILITY OF
# THE SOFTWARE, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
# TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE, OR NON-INFRINGEMENT. NVISO SHALL NOT BE LIABLE FOR
# ANY DAMAGES SUFFERED BY LICENSEE AS A RESULT OF USING, MODIFYING OR
# DISTRIBUTING THIS SOFTWARE OR ITS DERIVATIVES.
#


""" This fil is using an utility to augment an image, https://github.com/aleju/imgaug """


import os
import glob
import cv2

import imgaug as ia
from imgaug import augmenters as iaa
import numpy as np

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO


def tan_triggs_preprocessing(image, alpha=0.1, tau=10.0, gamma=0.2, sigma0=1, sigma1=2):

    # Tan-Triggs normalizacion
    if len(image.shape) > 1:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    a, b = image.shape
    I = gamma_correction(image, (0, 1), (0, 255), gamma)

    # Difference of Gaussians
    I = diff_of_gaussians(I, sigma0, sigma1)

    # tanh mapping
    I = tan_triggs_normalization(I, alpha, tau)

    I = normalize8(I)
    return np.uint8(I)


def tan_triggs_normalization(I, alpha, tau):

    # Contrast EQ
    # First Stage
    tmp = np.power(abs(I), alpha)
    meanI = np.mean(tmp)
    I = I / np.power(meanI, 1.0 / alpha)

    # Second Stage
    tmp = np.power(np.minimum(abs(I), tau), alpha)
    meanI = np.mean(tmp)
    I = I / np.power(meanI, 1.0 / alpha)
    I = tau * np.tanh(I / tau)

    return I


def gamma_correction(I, in_interval, out_interval, gamma):

    I = np.float64(I)
    a, b = I.shape
    I = adjust_range(I, in_interval)

    I = np.power(I, gamma)
    Y = adjust_range(I, out_interval)

    return Y


def adjust_range(I, interval=(0, 255)):

    I = np.float64(I)
    a, b = I.shape

    minNew = interval[0]
    maxNew = interval[1]

    maxOld = np.amax(I)
    minOld = np.amin(I)

    Y = ((maxNew - minNew) / (maxOld - minOld)) * (I - minOld) + minNew

    return Y


def diff_of_gaussians(I, sigma0, sigma1):

    # Difference of Gaussians
    kernel_size0 = int(2 * np.ceil(3 * sigma0) + 1)
    kernel_size1 = int(2 * np.ceil(3 * sigma1) + 1)

    gaussian0 = cv2.GaussianBlur(I, (kernel_size0, kernel_size0), sigma0)
    gaussian1 = cv2.GaussianBlur(I, (kernel_size1, kernel_size1), sigma1)
    return gaussian0 - gaussian1


def normalize8(I):

    I = np.float64(I)
    a, b = I.shape
    maxI = np.amax(I)
    minI = np.amin(I)

    Y = np.ceil(((I - minI) / (maxI - minI)) * 255)

    return Y


def augment_image(img, size, enable_tan_trigg=True, seed=None):

    # Augment images
    # Define our sequence of augmentation steps that will be applied to every image
    # All augmenters with per_channel=0.5 will sample one value _per image_
    # in 50% of all cases. In all other cases they will sample new values
    # _per channel_.
    seq = iaa.Sequential(
        [
            # execute 0 to 5 of the following (less important) augmenters per image
            # don't execute all of them, as that would often be way too strong
            iaa.SomeOf((0, 5),
                [
                    iaa.OneOf([
                        iaa.GaussianBlur((0, 3.0)),  # blur images with a sigma between 0 and 3.0
                        iaa.AverageBlur(k=(2, 7)),   # blur image using local means with kernel sizes between 2 and 7
                        iaa.MedianBlur(k=(3, 11)),   # blur image using local medians with kernel sizes between 2 and 7
                    ]),
                    iaa.Sharpen(alpha=(0, 1.0), lightness=(0.75, 1.5)),  # sharpen images
                    iaa.Emboss(alpha=(0, 1.0), strength=(0, 2.0)),       # emboss images
                    iaa.AdditiveGaussianNoise(loc=0, scale=(0.0, 0.05 * 255), per_channel=0.5),  # add gaussian noise to images
                    iaa.Invert(0.03, per_channel=True),  # invert color channels
                    iaa.Add((-5, 5), per_channel=0.3),   # change brightness of images (by -10 to 10 of original value)
                    iaa.AddToHueAndSaturation((-20, 20)),  # change hue and saturation
                    # either change the brightness of the whole image (sometimes
                    # per channel) or change the brightness of subareas
                    iaa.OneOf([
                        iaa.Multiply((0.5, 1.5), per_channel=0.5),
                        iaa.FrequencyNoiseAlpha(
                            exponent=(-4, 0),
                            first=iaa.Multiply((0.5, 1.5), per_channel=True),
                            second=iaa.ContrastNormalization((0.5, 2.0))
                        )
                    ]),
                    iaa.ContrastNormalization((0.5, 2.0), per_channel=0.5),  # improve or worsen the contrast
                    iaa.Grayscale(alpha=(0.0, 1.0))
                ],
                random_order=True
            )
        ],
        random_order=True
    )

    # Load image and apply tan triggs preprocessing
    imarr_orig = []
    imarr_aug = []
    imarr_tt = []
    for i in range(size):
        imarr_orig.append(img)

    # Set random seed
    np.random.seed(seed)
    ia.seed(seed)

    # Augment images
    imarr_aug = seq.augment_images(imarr_orig)

    if enable_tan_trigg:
        for im_aug in imarr_aug:
            # Preprocessing
            imarr_tt.append(tan_triggs_preprocessing(im_aug))

    return (imarr_aug, imarr_tt)


if __name__ == "__main__":

    # This is augmentation factor^2, 6 = 36
    augmentation_factor = 6
    augmentation_size = augmentation_factor * augmentation_factor
    output_augmented = True
    output_processed = False

    os.chdir("input")
    for filename in glob.glob("*.jpg"):

        img = cv2.imread(filename)

        (images_aug, images_tt) = augment_image(img, augmentation_size, output_processed)

        path_prefix = "../output/" + os.path.splitext(filename)[0]

        if output_augmented:

            for idx, image in enumerate(images_aug):

                # Save augmented images
                if output_augmented:
                    ret = cv2.imwrite(path_prefix + "_aug_" + str(idx) + os.path.splitext(filename)[1], images_aug[idx])
                    if not ret:
                        print("Failed to write image")

        for idx, image in enumerate(images_tt):

            # Save tan trigg processed images
            ret = cv2.imwrite(path_prefix + "_tt_" + str(idx) + os.path.splitext(filename)[1], images_tt[idx])
            if not ret:
                print("Failed to write image")
