"""
Reads L1 data
"""

import os

import ac3airborne
import xarray as xr

META = ac3airborne.get_flight_segments()


def read_amali_l1(flight_id):
    """
    Read AMALi l1 data
    """

    mission, platform, name = flight_id.split("_")
    date = META[mission][platform][flight_id]["date"].strftime("%Y%m%d")

    ds = xr.open_dataset(
        os.path.join(
            os.environ["PATH_SEC"],
            "data/ac3/amali/l1",
            f"{flight_id}_AMALi_l1_{date}.nc",
        )
    )

    return ds
