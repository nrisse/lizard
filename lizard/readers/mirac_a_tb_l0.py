"""
Read MiRAC-A TB level 0 files.
"""

import os

import ac3airborne
import xarray as xr

META = ac3airborne.get_flight_segments()


def read_mirac_a_tb_l0(flight_id):
    """
    Write MiRAC-A TB level 0 data to file
    """

    mission, platform, name = flight_id.split("_")
    date = META[mission][platform][flight_id]["date"].strftime("%Y%m%d")

    ds = xr.open_dataset(
        os.path.join(
            f"/data/obs/campaigns/{mission.lower()}/p5/mirac_radar/tb_l0",
            f"{flight_id}_MiRAC-A_tb_l0_{date}.nc",
        )
    )

    return ds
