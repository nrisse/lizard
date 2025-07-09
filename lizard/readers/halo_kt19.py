"""
Read HALO KT-19.
"""

import xarray as xr

from lizard.ac3airlib import day_of_flight


def read_halo_kt19(flight_id, version="v1.0"):
    """
    Reads HALO VELOX/KT-19 measurements at nadir.

    Parameters
    ----------
    flight_id: ac3airborne flight id

    Returns
    -------
    ds: xarray Dataset with KT-19 IR temperature
    """

    mission, platform, name = flight_id.split("_")
    date = day_of_flight(flight_id)

    ds = xr.open_dataset(
        f"/data/obs/campaigns/halo-ac3/halo/kt19/HALO-AC3_HALO_KT19_BT_{date.strftime('%Y%m%d')}_{name}_{version}.nc"
    )

    return ds
