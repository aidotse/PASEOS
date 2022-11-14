import numpy as np
import scipy
import rasterio

# [1] Massimetti, Francesco, et al. ""Volcanic hot-spot detection using SENTINEL-2:
# a comparison with MODIS–MIROVA thermal data series."" Remote Sensing 12.5 (2020):820."


def acquire_data(file_name):
    """Read an L1C Sentinel-2 image from a cropped TIF. The image is represented as TOA reflectance.

    Args:
        file_name (str): event ID.
    Raises:
        ValueError: impossible to find information on the database.

    Returns:
        np.array: array containing B8A, B11, B12 of a Seintel-2 L1C cropped tif.
    """

    with rasterio.open(file_name) as raster:
        img_np = raster.read()
        sentinel_img = img_np.astype(np.float32)

    sentinel_img = (
        sentinel_img.transpose(1, 2, 0) / 10000 + 1e-13
    )  # Diving for the default quantification value
    return sentinel_img


def s2pix_detector(
    sentinel_img,
    alpha_thr=[1.4, 1.2, 0.15],
    beta_thr=[2, 0.5, 0.5],
    S_thr=[1.2, 1, 1.5, 1],
    gamma_thr=[1, 1, 0.5],
):
    """Implements the first step of the one described in [1] by proving a filtered alert-map.

    Args:
        sentinel_img (numpy.array): sentinel image
        alpha_thr (list, optional): pixel-level value for calculation of alpha threshold map. Defaults to [1.4, 1.2, 0.15].
        beta_thr (list, optional): pixel-level value for calculation of beta threshold map. Defaults to [2, 0.5, 0.5].
        S_thr (list, optional): pixel-level value for calculation of S threshold map. Defaults to [1.2, 1, 1.5, 1].
        gamma_thr (list, optional): pixel-level value for calculation of gamma threshold map. Defaults to [1, 1, 0.5].

    Returns:
        numpy.array: filtered alert_matrix threshold map.
        list: list of bounding boxes.
    """

    def get_thresholds(
        sentinel_img,
        alpha_thr=[1.4, 1.2, 0.15],
        beta_thr=[2, 0.5, 0.5],
        S_thr=[1.2, 1, 1.5, 1],
        gamma_thr=[1, 1, 0.5],
    ):
        """It returns the alpha, beta, gamma and S threshold maps for each band as described in [1]

        Args:
            sentinel_img (np.arraya): sentinel image
            alpha_thr (list, optional): pixel-level value for calculation of alpha threshold map. Defaults to [1.4, 1.2, 0.15].
            beta_thr (list, optional): pixel-level value for calculation of beta threshold map. Defaults to [2, 0.5, 0.5].
            S_thr (list, optional): pixel-level value for calculation of S threshold map. Defaults to [1.2, 1, 1.5, 1].
            gamma_thr (list, optional): pixel-level value for calculation of gamma threshold map. Defaults to [1, 1 , 0.5].

        Returns:
            np.array: alpha threshold map.
            np.array: beta threshold map.
            np.array: S threshold map.
            np.array: gamma threshold map.
        """

        def check_surrounded(img):
            weight = np.array([[1.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 1.0]])

            img_pad = np.pad(img, ((1, 1),), mode="constant", constant_values=(1, 1))
            surrounded = scipy.signal.convolve2d(img_pad, weight, mode="valid")
            surrounded[surrounded < 8] = 0
            surrounded[surrounded == 8] = 1

            return surrounded

        alpha = np.logical_and(
            np.where(sentinel_img[:, :, 2] >= alpha_thr[2], 1, 0),
            np.logical_and(
                np.where(
                    sentinel_img[:, :, 2] / sentinel_img[:, :, 1] >= alpha_thr[0], 1, 0
                ),
                np.where(
                    sentinel_img[:, :, 2] / sentinel_img[:, :, 0] >= alpha_thr[1], 1, 0
                ),
            ),
        )
        beta = np.logical_and(
            np.where(
                sentinel_img[:, :, 1] / sentinel_img[:, :, 0] >= beta_thr[0], 1, 0
            ),
            np.logical_and(
                np.where(sentinel_img[:, :, 1] >= beta_thr[1], 1, 0),
                np.where(sentinel_img[:, :, 2] >= beta_thr[2], 1, 0),
            ),
        )
        S = np.logical_or(
            np.logical_and(
                np.where(sentinel_img[:, :, 2] >= S_thr[0], 1, 0),
                np.where(sentinel_img[:, :, 0] <= S_thr[1], 1, 0),
            ),
            np.logical_and(
                np.where(sentinel_img[:, :, 1] >= S_thr[2], 1, 0),
                np.where(sentinel_img[:, :, 0] >= S_thr[3], 1, 0),
            ),
        )
        alpha_beta_logical_surrounded = check_surrounded(np.logical_or(alpha, beta))
        gamma = np.logical_and(
            np.logical_and(
                np.logical_and(
                    np.where(sentinel_img[:, :, 2] >= gamma_thr[0], 1, 0),
                    np.where(sentinel_img[:, :, 2] >= gamma_thr[1], 1, 0),
                ),
                np.where(sentinel_img[:, :, 0] >= gamma_thr[2], 1, 0),
            ),
            alpha_beta_logical_surrounded,
        )
        return alpha, beta, S, gamma

    def get_alert_matrix_and_thresholds(
        sentinel_img,
        alpha_thr=[1.4, 1.2, 0.15],
        beta_thr=[2, 0.5, 0.5],
        S_thr=[1.2, 1, 1.5, 1],
        gamma_thr=[1, 1, 0.5],
    ):
        """It calculates the alert-matrix for a certain image.

        Args:
            sentinel_img (numpy.array): sentinel image
            alpha_thr (list, optional): pixel-level value for calculation of alpha threshold map. Defaults to [1.4, 1.2, 0.15].
            beta_thr (list, optional): pixel-level value for calculation of beta threshold map. Defaults to [2, 0.5, 0.5].
            S_thr (list, optional): pixel-level value for calculation of S threshold map. Defaults to [1.2, 1, 1.5, 1].
            gamma_thr (list, optional): pixel-level value for calculation of gamma threshold map. Defaults to [1, 1, 0.5].

        Returns:
            numpy.array: alert_matrix threshold map.
            numpy.array: alpha threshold map.
            numpy.array: beta threshold map.
            numpy.array: S threshold map.
            numpy.array: gamma threshold map.
        """

        alpha, beta, S, gamma = get_thresholds(
            sentinel_img, alpha_thr, beta_thr, S_thr, gamma_thr
        )
        alert_matrix = np.logical_or(
            np.logical_or(np.logical_or(alpha, beta), gamma), S
        )
        return alert_matrix, alpha, beta, S, gamma

    def cluster_9px(img):
        """It performs the convolution to detect clusters of 9 hot pixels (current pixel and 8 surrounding pixels) are at 1.

        Args:
            img (numpy.array): input alert-matrix

        Returns:
            numpy.array: convoluted alert-map
        """

        weight = np.array([[1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]])

        img_pad = np.pad(img, ((1, 1),), mode="constant", constant_values=(0, 0))
        surrounded = scipy.signal.convolve2d(img_pad, weight, mode="valid")

        return surrounded

    alert_matrix, _, _, _, _ = get_alert_matrix_and_thresholds(
        sentinel_img, alpha_thr, beta_thr, S_thr, gamma_thr
    )
    filtered_alert_matrix = cluster_9px(alert_matrix)
    filtered_alert_matrix[filtered_alert_matrix < 9] = 0
    filtered_alert_matrix[filtered_alert_matrix == 9] = 1

    return filtered_alert_matrix