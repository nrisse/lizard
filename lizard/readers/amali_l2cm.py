"""
Reads L2 cloud mask
"""

import os

import ac3airborne
import xarray as xr

META = ac3airborne.get_flight_segments()


def read_amali_l2cm(flight_id):
    """
    Read AMALi l2 cloud mask
    """

    mission, platform, name = flight_id.split("_")
    date = META[mission][platform][flight_id]["date"].strftime("%Y%m%d")

    ds = xr.open_dataset(
        os.path.join(
            os.environ["PATH_SEC"],
            "data/ac3/amali/l2_cm",
            f"{flight_id}_AMALi_l2_cm_{date}.nc",
        )
    )

    return ds
