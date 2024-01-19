"""
Reads WALES data
"""

import os

import xarray as xr

from lizard.ac3airlib import day_of_flight


def read_wales(flight_id, product="wv"):
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
            f"obs/campaigns/{mission.lower()}/{platform.lower()}/wales/",
            date.strftime(r"%Y%m%d"),
            f"{mission}_{platform}_WALES_{product}_{date.strftime(r'%Y%m%d')}_{name}"
            "_V2.0.nc",
        )
    )

    return ds
