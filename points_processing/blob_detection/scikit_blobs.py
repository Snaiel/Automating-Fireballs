from math import sqrt
import skimage as ski
from skimage.feature import blob_dog, blob_log, blob_doh
from numpy import ndarray

import matplotlib.pyplot as plt


def log_blob_detection(image: ndarray) -> ndarray:
    blobs_log = blob_log(image, max_sigma=30, num_sigma=20, threshold=0.025)
    blobs_log[:, 2] = blobs_log[:, 2] * sqrt(2)
    return blobs_log


def log_blob_detection_from_file(image_path: str) -> ndarray:
    return log_blob_detection(ski.io.imread(image_path))


def dog_blob_detection(image: ndarray) -> ndarray:
    blobs_dog = blob_dog(image, max_sigma=30, threshold=0.025)
    blobs_dog[:, 2] = blobs_dog[:, 2] * sqrt(2)
    return blobs_dog


def dog_blob_detection_from_file(image_path: str) -> ndarray:
    return dog_blob_detection(ski.io.imread(image_path))


def doh_blob_detection(image: ndarray) -> ndarray:
    blobs_doh = blob_doh(image, max_sigma=30, threshold=.01)
    return blobs_doh


def doh_blob_detection_from_file(image_path: str) -> ndarray:
    return doh_blob_detection(ski.io.imread(image_path))


def main():
    from pathlib import Path

    file_path = Path(__file__)
    image_path = Path(file_path.parents[1], 'fireball_images', 'cropped', '044_2021-10-28_064629_E_DSC_0731-G_cropped.jpeg')

    image = ski.io.imread(image_path)
    print(type(image))

    blobs_log = log_blob_detection(image)
    blobs_dog = dog_blob_detection(image)
    blobs_doh = doh_blob_detection(image)
    
    blobs_list = [blobs_log, blobs_dog, blobs_doh]
    colors = ['yellow', 'lime', 'red']
    titles = ['Laplacian of Gaussian', 'Difference of Gaussian', 'Determinant of Hessian']
    sequence = zip(blobs_list, colors, titles)

    fig, axes = plt.subplots(1, 3, figsize=(9, 3), sharex=True, sharey=True)
    ax = axes.ravel()

    for idx, (blobs, color, title) in enumerate(sequence):
        ax[idx].set_title(title)
        ax[idx].imshow(image, cmap='gray')
        for blob in blobs:
            y, x, r = blob
            c = plt.Circle((x, y), r, color=color, linewidth=1, fill=False)
            ax[idx].add_patch(c)
        ax[idx].set_axis_off()

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()