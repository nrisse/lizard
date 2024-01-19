"""
Reads satellite tracks
"""


import os

import xarray as xr
from dotenv import load_dotenv

load_dotenv()


def read_sat_tracks(t0=None, t1=None):
    """
    Reads satellite tracks

    Parameters
    -------
    t0: start time
    t1: end time
    """

    ds = xr.open_dataset(
        os.path.join(os.environ["PATH_SAT"], "tracks/sat_tracks.nc")
    )

    if t0 is not None and t1 is not None:
        ds = ds.sel(time=slice(t0, t1))

    return ds
