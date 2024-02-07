import numpy as np
import scipy
import rasterio
from skimage.measure import label, regionprops

# [1] Massimetti, Francesco, et al. ""Volcanic hot-spot detection using SENTINEL-2:
# a comparison with MODIS–MIROVA thermal data series."" Remote Sensing 12.5 (2020):820."
# The code of the function "s2pix_detector" and its subfunctions was taken and reimplemented by using numpy
# from the project "sentinel2_l0" dataset, which will be released soon.

# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>.


def acquire_data(file_name):
    """Read an L1C Sentinel-2 image from a cropped TIF. The image is represented as TOA reflectance.

    Args:
        file_name (str): event ID.
    Raises:
        ValueError: impossible to find information on the database.

    Returns:
        np.array: array containing B8A, B11, B12 of a Seintel-2 L1C cropped tif.
        dictionary: dictionary containing lat and lon for every image point.
    """

    with rasterio.open(file_name) as raster:
        img_np = raster.read()
        sentinel_img = img_np.astype(np.float32)
        height = sentinel_img.shape[1]
        width = sentinel_img.shape[2]
        cols, rows = np.meshgrid(np.arange(width), np.arange(height))
        xs, ys = rasterio.transform.xy(raster.transform, rows, cols)
        lons = np.array(ys)
        lats = np.array(xs)
        coords_dict = {"lat": lats, "lon": lons}

    sentinel_img = (
        sentinel_img.transpose(1, 2, 0) / 10000 + 1e-13
    )  # Diving for the default quantification value

    return sentinel_img, coords_dict


def check_surrounded(img):
    """Function to check for each pixel if all the surrounding pixels are hot pixel. Please, check [1].

    Args:
        img (np.array): sentinel2 L1C image.

    Returns:
        np.array: binary map whose unitary pixels are those for which the surrounding conditions is true.
    """
    weight = np.array([[1.0, 1.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 1.0]])

    img_pad = np.pad(img, ((1, 1),), mode="constant", constant_values=(1, 1))
    surrounded = scipy.signal.convolve2d(img_pad, weight, mode="valid")
    surrounded[surrounded < 8] = 0
    surrounded[surrounded == 8] = 1

    return surrounded


def get_thresholds(
    sentinel_img,
    alpha_thr=[1.4, 1.2, 0.15],
    beta_thr=[2, 0.5, 0.5],
    S_thr=[1.2, 1, 1.5, 1],
    gamma_thr=[1, 1, 0.5],
):
    """It returns the alpha, beta, gamma and S threshold maps for each band as described in [1].

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

    alpha = np.logical_and(
        np.where(sentinel_img[:, :, 2] >= alpha_thr[2], 1, 0),
        np.logical_and(
            np.where(sentinel_img[:, :, 2] / sentinel_img[:, :, 1] >= alpha_thr[0], 1, 0),
            np.where(sentinel_img[:, :, 2] / sentinel_img[:, :, 0] >= alpha_thr[1], 1, 0),
        ),
    )
    beta = np.logical_and(
        np.where(sentinel_img[:, :, 1] / sentinel_img[:, :, 0] >= beta_thr[0], 1, 0),
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
        alpha_thr (list, optional): pixel-level value for alpha threshold map calculation. Defaults to [1.4, 1.2, 0.15].
        beta_thr (list, optional): pixel-level value for beta threshold map calculation. Defaults to [2, 0.5, 0.5].
        S_thr (list, optional): pixel-level value for S threshold map calculation. Defaults to [1.2, 1, 1.5, 1].
        gamma_thr (list, optional): pixel-level value for gamma threshold map calculation. Defaults to [1, 1, 0.5].

    Returns:
        numpy.array: alert_matrix threshold map.
        numpy.array: alpha threshold map.
        numpy.array: beta threshold map.
        numpy.array: S threshold map.
        numpy.array: gamma threshold map.
    """

    alpha, beta, S, gamma = get_thresholds(sentinel_img, alpha_thr, beta_thr, S_thr, gamma_thr)
    alert_matrix = np.logical_or(np.logical_or(np.logical_or(alpha, beta), gamma), S)
    return alert_matrix, alpha, beta, S, gamma


def cluster_9px(img):
    """It performs a simplified 9-pixel clustering to filter the hotmap by performing a convolution.

    Args:
        img (numpy.array): input alert-matrix

    Returns:
        numpy.array: convoluted alert-map
    """

    weight = np.array([[1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]])

    img_pad = np.pad(img, ((1, 1),), mode="constant", constant_values=(0, 0))
    surrounded = scipy.signal.convolve2d(img_pad, weight, mode="valid")

    return surrounded


def get_event_bounding_box(event_hotmap, coords_dict):
    """Returns the bounding box and their top-left, bottom-right corners coordinates for each cluster of 1 in the event_hotmap.

    Args:
        event_hotmap (torch.tensor): event hotmap. Pixels = 1 indicate event.
        coords_dict (dict): {"lat" : lat, lon : "lon"}, containing coordinates for each pixel in the hotmap.

    Returns:
        skimage.bb: bounding box.
        list: list of coordinates of top-left, bottom-right corners for each cluster of events in the hotmap.
    """

    lbl = label(event_hotmap)
    props = regionprops(lbl)
    event_bbox_coordinates_list = []
    for prop in props:
        lat = np.array(coords_dict["lat"])
        lon = np.array(coords_dict["lon"])

        bbox_coordinates = [
            [lat[prop.bbox[0], prop.bbox[1]], lon[prop.bbox[0], prop.bbox[1]]],
            [lat[prop.bbox[2], prop.bbox[3]], lon[prop.bbox[2], prop.bbox[3]]],
        ]
        event_bbox_coordinates_list.append(bbox_coordinates)

    return props, event_bbox_coordinates_list


def s2pix_detector(
    sentinel_img,
    coords_dict,
    alpha_thr=[1.4, 1.2, 0.15],
    beta_thr=[2, 0.5, 0.5],
    S_thr=[1.2, 1, 1.5, 1],
    gamma_thr=[1, 1, 0.5],
):
    """Implements the first step of the one described in [1] by proving a filtered alert-map.

    Args:
        sentinel_img (numpy.array): sentinel2 L1C image.
        dictionary: dictionary containing lat and lon for every image point.
        alpha_thr (list, optional): pixel-level value for alpha threshold map calculation. Defaults to [1.4, 1.2, 0.15].
        beta_thr (list, optional): pixel-level value for beta threshold map calculation. Defaults to [2, 0.5, 0.5].
        S_thr (list, optional): pixel-level value for calculation of S threshold map. Defaults to [1.2, 1, 1.5, 1].
        gamma_thr (list, optional): pixel-level value for calculation of gamma threshold map. Defaults to [1, 1, 0.5].

    Returns:
        list: [list of bounding boxes objects, list of bounding boxes coordinates]
    """

    alert_matrix, _, _, _, _ = get_alert_matrix_and_thresholds(
        sentinel_img, alpha_thr, beta_thr, S_thr, gamma_thr
    )
    filtered_alert_matrix = cluster_9px(alert_matrix)
    filtered_alert_matrix[filtered_alert_matrix < 9] = 0
    filtered_alert_matrix[filtered_alert_matrix == 9] = 1
    bbox_info = get_event_bounding_box(filtered_alert_matrix, coords_dict)

    return bbox_info
