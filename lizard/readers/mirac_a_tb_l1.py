"""
Read MiRAC-A TB level 1 files.
"""

import os

import ac3airborne
import xarray as xr

META = ac3airborne.get_flight_segments()


def read_mirac_a_tb_l1(flight_id):
    """
    Read MiRAC-A TB level 1 data
    """

    mission, platform, name = flight_id.split("_")
    date = META[mission][platform][flight_id]["date"].strftime("%Y%m%d")

    ds = xr.open_dataset(
        os.path.join(
            f"/data/obs/campaigns/{mission.lower()}/p5/mirac_radar/tb_l1",
            f"{flight_id}_MiRAC-A_tb_l1_{date}.nc",
        )
    )

    return ds
