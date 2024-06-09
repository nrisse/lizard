"""
Read radiosonde data
"""

import datetime
import os
from glob import glob

import ac3airborne
import pandas as pd
import xarray as xr
from dotenv import load_dotenv

load_dotenv()

META = ac3airborne.get_flight_segments()


def read_radiosonde(flight_id=None, time=None):
    """
    Reads radiosonde closest to takeoff time of research flight or a certain
    time.

    Parameters
    ----------
    flight_id: ac3airborne flight id
    time: time around which the closest radiosonde will be searched

    Returns
    -------
    ds: xarray datset of radiosonde
    """

    if flight_id is not None and time is None:
        mission, platform, name = flight_id.split("_")
        time = META[mission][platform][flight_id]["takeoff"]

    else:
        print(time)
        time = pd.Timestamp(time)

    # find the closest sounding from takeoff time
    files = glob(
        os.path.join(
            os.environ["PATH_SEC"],
            "data/radiosondes/ny_alesund/*.nc",
        )
    )

    dates = [
        datetime.datetime.strptime(file[-15:-3], "%Y%m%d%H%M")
        for file in files
    ]
    date_rs = min(dates, key=lambda x: abs(x - time)).strftime("%Y%m%d%H%M")
    ds = xr.open_dataset(
        os.path.join(
            os.environ["PATH_SEC"],
            f"data/radiosondes/ny_alesund/radiosonde_ny_alesund_{date_rs}.nc",
        )
    )

    return ds


def read_merged_radiosonde():
    """
    Reads merged radiosonde dataset from Ny-Alesund.
    """

    ds = xr.open_dataset(
        os.path.join(
            os.environ["PATH_SEC"],
            "data",
            "radiosondes",
            "ny_alesund",
            "merge",
            "radiosonde_ny_alesund_merge.nc",
        )
    )

    return ds
