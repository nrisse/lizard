"""
Reads ERA-5 single and surface levels data
"""

import os

import pandas as pd
import xarray as xr
from dotenv import load_dotenv

load_dotenv()


def read_era5_single_levels(time, roi=None):
    """
    Reads ERA-5 single levels data for a given time step.

    Parameters
    ----------
    time: day for which ERA-5 data is imported.
    roi: region of interest

    Returns
    -------
    xr.Dataset of ERA-5 single levels data.
    """

    ds = xr.open_dataset(
        os.path.join(
            os.environ["PATH_SEC"],
            "data/era5/",
            pd.Timestamp(time).strftime("%Y/%m"),
            f'era5-single-levels_60n_{pd.Timestamp(time).strftime("%Y%m%d")}.nc',
        )
    )

    if roi is not None:
        ds = ds.sel(
            longitude=slice(roi[0], roi[1]), latitude=slice(roi[3], roi[2])
        )

    return ds


def read_era5_pressure_levels(time, roi=None):
    """
    Reads ERA-5 pressure levels data for a given time step.

    Parameters
    ----------
    time: day for which ERA-5 data is imported.
    roi: region of interest

    Returns
    -------
    xr.Dataset of ERA-5 single levels data.
    """

    ds = xr.open_dataset(
        os.path.join(
            os.environ["PATH_SEC"],
            "data/era5/",
            pd.Timestamp(time).strftime("%Y/%m"),
            f'era5-pressure-levels_60n_{pd.Timestamp(time).strftime("%Y%m%d")}.nc',
        )
    )

    if roi is not None:
        ds = ds.sel(
            longitude=slice(roi[0], roi[1]), latitude=slice(roi[3], roi[2])
        )

    return ds
