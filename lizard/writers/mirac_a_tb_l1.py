"""
Write MiRAC-A TB level 1 files.
"""

import os

import ac3airborne

META = ac3airborne.get_flight_segments()


def write_mirac_a_tb_l1(ds, flight_id):
    """
    Write MiRAC-A TB level 1 data to file
    """

    mission, platform, name = flight_id.split("_")
    date = META[mission][platform][flight_id]["date"].strftime("%Y%m%d")

    ds.to_netcdf(
        os.path.join(
            f"/data/obs/campaigns/{mission.lower()}/p5/mirac_radar/tb_l1",
            f"{flight_id}_MiRAC-A_tb_l1_{date}.nc",
        )
    )
