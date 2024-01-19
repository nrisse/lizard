"""
Read satellite tb that way extracted along flight track
"""

import os

import xarray as xr


def read_sat_at_aircraft(flight_id):
    """
    Read satellite tb that was extracted along flight track

    Parameters
    ----------
    flight_id

    Returns
    -------
    dataset with satellite tb along flight track
    """

    ds = xr.open_dataset(
        os.path.join(
            os.environ["PATH_SEC"],
            "data/sea_ice_emissivity/sat_flight_track",
            f"{flight_id}_gpm_l1c.nc",
        )
    )

    return ds


def read_sat_at_aircraft_unique(flight_id):
    """
    Read satelite observations that align with flight track

    Parameters
    ----------
    flight_id

    Returns
    -------
    dataset with satellite tb footprints that align with flight track
    """

    ds = xr.open_dataset(
        os.path.join(
            os.environ["PATH_SEC"],
            "data/sea_ice_emissivity/sat_flight_track",
            f"{flight_id}_gpm_l1c_unique_ancil.nc",
        )
    )

    return ds
