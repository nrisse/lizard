"""
Reader for AMSR2 sea ice concentration hdf files
"""

import os

import pandas as pd
import xarray as xr

from pyhdf.SD import SD, SDC


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

    hdf_grid = SD(
        os.path.join(path, "LongitudeLatitudeGrid-n6250-Arctic.hdf"), SDC.READ
    )
    hdf_sic = SD(
        os.path.join(
            path,
            "asi-AMSR2-n6250-"
            + pd.Timestamp(date).strftime("%Y%m%d")
            + "-v5.4.hdf",
        ),
        SDC.READ,
    )

    lon = hdf_grid.select(0).get()
    lat = hdf_grid.select(1).get()
    sic = hdf_sic.select(0).get()

    # combineas xarray dataset
    ds = xr.Dataset()
    ds.coords["lon"] = (("x", "y"), lon)
    ds.coords["lat"] = (("x", "y"), lat)
    ds["sic"] = (("x", "y"), sic)

    return ds
