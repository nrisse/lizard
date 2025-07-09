"""
Reads WALES data
"""

import os
from glob import glob

import xarray as xr
import numpy as np

from lizard.ac3airlib import day_of_flight


def preprocess_wales(ds):
    altitude = np.arange(0, 10000, 15)
    ds = ds.sortby("altitude")
    ds = ds.interp(altitude=altitude, method="linear", assume_sorted=True)
    ds = round_time(ds)

    return ds


def round_time(ds):
    ds["time"] = ds["time"].dt.round("s")
    _, ix = np.unique(ds["time"], return_index=True)
    ds = ds.isel(time=ix)
    return ds


def read_wales(flight_id, product, round_seconds=True):
    """
    Reads WALES water vapor data for specific flight id

    Parameters
    ----------
    flight_id : str
        Ac3airborne flight id
    product : str
        Product to read. Default is "wv" for water vapor. For other options see
        the data folder.

    Returns
    -------
    ds : xarray.Dataset
        WALES water vapor data
    """

    mission, platform, name = flight_id.split("_")
    date = day_of_flight(flight_id)

    ds = xr.open_dataset(
        os.path.join(
            os.environ["PATH_DAT"],
            f"obs/campaigns/halo-ac3/halo/wales/",
            f"{mission}_{platform}_WALES_{product}_{date.strftime(r'%Y%m%d')}_{name}"
            "_V2.0.nc",
        )
    )

    if round_seconds:
        ds = round_time(ds)

    return ds


def read_wales_dask(product, round_seconds=True):
    """
    Read all WALES data into a single dask array
    """

    files = glob(
        os.path.join(
            os.environ["PATH_DAT"],
            f"obs/campaigns/halo-ac3/halo/wales/",
            f"HALO-AC3_HALO_WALES_{product}_*_*_V2.0.nc",
        )
    )

    ds = xr.open_mfdataset(files, preprocess=preprocess_wales)

    return ds
