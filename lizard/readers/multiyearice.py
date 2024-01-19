"""
Reads multi-year ice data from University of Bremen
"""

import os

import pandas as pd
import xarray as xr
from osgeo import gdal


def read_myi(date):
    """
    Reads multi-year ice data from University of Bremen

    Parameters
    ----------
    date : datetime.datetime
        Date of the data to be read

    Returns
    -------
    ds : xarray.Dataset
        Dataset with multi-year ice data
    """

    date_str = pd.Timestamp(date).strftime("%Y%m%d")

    lon = gdal.Open(
        os.path.join(
            os.environ["PATH_SEC"], "data/sat/multiyearice/north_lon_12km.hdf"
        )
    ).ReadAsArray()

    lat = gdal.Open(
        os.path.join(
            os.environ["PATH_SEC"], "data/sat/multiyearice/north_lat_12km.hdf"
        )
    ).ReadAsArray()

    ds = xr.open_dataset(
        os.path.join(
            os.environ["PATH_SEC"],
            f"data/sat/multiyearice/MultiYearIce-Arctic-{date_str}v1.1.nc",
        )
    )

    # this was necessary, grid was flipped
    ds["lon"] = (("X", "Y"), lon[::-1, :])
    ds["lat"] = (("X", "Y"), lat[::-1, :])

    return ds
