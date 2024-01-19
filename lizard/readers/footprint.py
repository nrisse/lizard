"""
Read file with footprint location. These files are combined afterwards with
the lidar data.

The data was calculated within the sea ice emissivity project based on the GPS
data and a digital terrain model.
"""

import os

import ac3airborne
import xarray as xr

META = ac3airborne.get_flight_segments()


def read_footprint(flight_id):
    """
    Write footprint dataset file.

    Parameters
    ----------
    flight_id: research flight id from ac3airborne.

    Returns
    -------
    ds: footprint dataset
    """

    mission, platform, name = flight_id.split("_")
    date = META[mission][platform][flight_id]["date"].strftime("%Y%m%d")

    ds = xr.open_dataset(
        os.path.join(
            os.environ["PATH_SEC"],
            "data/sea_ice_emissivity/footprint",
            f"footprint_{flight_id}_{date}.nc",
        )
    )

    return ds
