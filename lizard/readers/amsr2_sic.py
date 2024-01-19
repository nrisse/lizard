"""
Reader for AMSR2 sea ice concentration hdf files
"""


import os

import pandas as pd
import xarray as xr
from osgeo import gdal


def read_amsr2_sic(date, path):
    """
    Read hdf files of sea ice concentration from University of Bremen

    Input
    -------
    date:  date (yyyymmdd) for which sea ice should be retrieved

    Returns
    -------
    xarray.Dataset with sea ice concentration
    """

    lon = gdal.Open(
        'HDF4_SDS:UNKNOWN:"'
        + os.path.join(path, "LongitudeLatitudeGrid-n6250-Arctic.hdf")
        + '":0'
    ).ReadAsArray()

    lat = gdal.Open(
        'HDF4_SDS:UNKNOWN:"'
        + os.path.join(path, "LongitudeLatitudeGrid-n6250-Arctic.hdf")
        + '":1'
    ).ReadAsArray()

    sic = gdal.Open(
        os.path.join(
            path,
            "asi-AMSR2-n6250-"
            + pd.Timestamp(date).strftime("%Y%m%d")
            + "-v5.4.hdf",
        )
    ).ReadAsArray()

    # combineas xarray dataset
    ds = xr.Dataset()
    ds.coords["lon"] = (("x", "y"), lon)
    ds.coords["lat"] = (("x", "y"), lat)
    ds["sic"] = (("x", "y"), sic)

    # close dataset
    del sic

    return ds
