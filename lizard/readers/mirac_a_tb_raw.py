"""
Read raw MiRAC-A TB for a given research flight
"""

import os
from glob import glob

import ac3airborne
import numpy as np
import xarray as xr

meta = ac3airborne.get_flight_segments()


def read_mirac_a_tb_raw(flight_id):
    """
    Reads MiRAC-A tb from raw_rpg files

    Parameters
    ----------
    flight_id

    Returns
    -------
    xarray.Dataset with tb as a function of time
    """

    mission, platform, name = flight_id.split("_")
    flight = meta[mission][platform][flight_id]
    date = flight["date"]

    files = glob(
        os.path.join(
            os.environ["PATH_DAT"],
            f"obs/campaigns",
            mission.lower(),
            "p5/mirac_radar/raw/",
            date.strftime("%Y/%m/%d"),
            f'*{date.strftime("%y%m%d")}*.nc',
        )
    )

    ds_lst = []
    for file in files:
        ds_lst.append(xr.open_dataset(file)[["tb", "t_rec", "sample_tms"]])

    if len(ds_lst) == 0:
        return

    ds = xr.merge(ds_lst)

    # add milliseconds
    ds["time"] = ds["time"] + ds.sample_tms.values.astype("timedelta64[ms]")

    # sort by time
    ds = ds.sel(time=np.sort(ds.time))

    # get brightness temperature at full seconds (same was done for lidar)
    t = ds.time.values.astype("datetime64[s]")
    t = np.sort(np.unique(np.append(t, t + np.timedelta64(1, "s"))))
    ds = ds.interp(
        time=t,
        method="linear",
        kwargs=dict(fill_value=np.nan, bounds_error=False),
    )

    # drop times, where extrapolation was needed (all values are nan)
    ds = ds.sel(time=~ds["tb"].isnull())

    # reduce to flight time
    ds = ds.sel(time=slice(flight["takeoff"], flight["landing"]))

    # remove millisecond variable
    ds = ds.drop_vars("sample_tms")

    return ds
