"""
Reads reprojected NASA worldview image
"""

import os

from osgeo import gdal

from ..ac3airlib import day_of_flight


def read_worldview(flight_id):
    """

    Parameters
    ----------
    flight_id: ac3airborne flight id

    Returns
    -------
    img: nasa worldview image
    extent: image extent to plot on cartopy map
    """

    mission, platform, name = flight_id.split("_")

    if platform == "P5":
        file = os.path.join(
            os.environ["PATH_DAT"],
            "obs/campaigns/",
            mission.lower(),
            "auxiliary/modis/",
            "worldview_terra_modis_corrected_reflectance_true_color_250m",
            f'snapshot-{day_of_flight(flight_id).strftime("%Y-%m-%d")}'
            f"T00_00_00Z_reprojected.tiff",
        )

    else:
        file = os.path.join(
            os.environ["PATH_DAT"],
            "obs/campaigns/",
            mission.lower(),
            "auxiliary/modis/",
            "worldview_terra_modis_corrected_reflectance_true_color_500m",
            f'snapshot-{day_of_flight(flight_id).strftime("%Y-%m-%d")}'
            f"T00_00_00Z_reprojected.tiff",
        )

    data, extent = read_rgb(file)

    # change background from black to white
    ix = data.sum(axis=0) == 0
    data[..., ix] = 255

    return data, extent


def read_rgb(file):
    """
    Reads RGB satellite image from GeoTIFF format. The RGB
    channels are transposed for plotting in Python.

    Parameters
    ----------
    file: filename of GeoTIFF image

    Returns
    -------
    data: image as numpy array (width, height, channel)
    extent: image extent
    """

    img = gdal.Open(file)
    data = img.ReadAsArray()

    # get extent
    gt = img.GetGeoTransform()
    extent = (
        gt[0],
        gt[0] + img.RasterXSize * gt[1],
        gt[3] + img.RasterYSize * gt[5],
        gt[3],
    )

    # transpose as required for matplotlib
    data = data.transpose((1, 2, 0))

    return data, extent
